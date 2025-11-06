"""
WEAR Gateway Client
"""

import base64
import json
import time
from dataclasses import dataclass, asdict
from typing import Optional, Callable, TypeVar, Dict, Any
import logging

import httpx

from .errors import WearError, WearErrorResponse
from .types import (
    StartRunResponse,
    LogCostRequest,
    LogCostResponse,
    LogAccessRequest,
    LogAccessResponse,
    FinishRunRequest,
    FinishRunResponse,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


# Retry configuration
MAX_RETRIES = 3
INITIAL_DELAY_MS = 100
MAX_DELAY_MS = 5000


def _is_retryable_error(status_code: int) -> bool:
    """Check if error is retryable (5xx status codes)"""
    return 500 <= status_code < 600


def _get_backoff_delay(attempt: int) -> float:
    """Calculate exponential backoff delay in seconds"""
    delay_ms = INITIAL_DELAY_MS * (2 ** (attempt - 1))
    delay_ms = min(delay_ms, MAX_DELAY_MS)
    return delay_ms / 1000.0


def _extract_agent_id_from_jwt(jwt: str) -> str:
    """Extract agent ID from JWT (simple implementation)"""
    try:
        payload = jwt.split('.')[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = json.loads(base64.b64decode(payload))
        return decoded.get('aid') or decoded.get('agent_id') or 'unknown'
    except Exception:
        return 'unknown'


@dataclass
class WearClientOptions:
    """SDK configuration options"""

    base_url: str
    """Base URL of the WEAR Gateway (e.g., https://wear-gateway-staging-xxx.run.app)"""

    timeout_ms: int = 10000
    """Request timeout in milliseconds (default: 10000)"""


class WearClient:
    """
    WEAR Gateway Client

    Implements the WEAR protocol with required headers:
    - Authorization: Bearer <jwt>
    - X-WEAR-Agent-ID: <agent_id>
    """

    def __init__(self, options: WearClientOptions) -> None:
        self.base_url = options.base_url.rstrip("/")
        self.timeout = options.timeout_ms / 1000.0  # Convert to seconds
        self._client = httpx.Client(timeout=self.timeout)

    def __enter__(self) -> "WearClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client"""
        self._client.close()

    def start_run(self, agent_id: str, jwt: str) -> StartRunResponse:
        """
        Start a new agent run

        Args:
            agent_id: The agent identifier
            jwt: JWT token from /v1/agents/token

        Returns:
            StartRunResponse with run_id and started_at

        Raises:
            WearError: On policy denial, budget exceeded, or other errors
        """
        response = self._client.post(
            f"{self.base_url}/v1/runs/start",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt}",
                "X-WEAR-Agent-ID": agent_id,
            },
            json={"agent_id": agent_id},
        )

        if not response.is_success:
            error_body = self._parse_error_response(response)
            raise WearError(
                self._format_error_message("start_run", response.status_code, error_body),
                response.status_code,
                error_body,
            )

        data = response.json()
        return StartRunResponse(
            run_id=data["run_id"],
            started_at=data["started_at"],
            correlation_id=data.get("correlation_id"),
        )

    def _parse_error_response(self, response: httpx.Response) -> WearErrorResponse:
        """Parse error response body safely"""
        try:
            text = response.text
            if not text:
                return WearErrorResponse()
            data = json.loads(text)
            return WearErrorResponse.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return WearErrorResponse()

    def log_cost(
        self, run_id: str, body: LogCostRequest, jwt: str
    ) -> LogCostResponse:
        """
        Log cost information for a run

        Args:
            run_id: Run identifier (required)
            body: Cost details
            jwt: JWT token

        Returns:
            LogCostResponse with ok status

        Raises:
            WearError: If run_id is missing or on API errors
        """
        if not run_id:
            raise WearError("log_cost requires run_id", 400, WearErrorResponse(error="missing_run_id"))

        return self._retryable_request(
            "log_cost",
            lambda: self._client.post(
                f"{self.base_url}/v1/runs/log-cost",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {jwt}",
                    "X-WEAR-Agent-ID": _extract_agent_id_from_jwt(jwt),
                    "X-WEAR-Run-ID": run_id,
                },
                json=asdict(body),
                timeout=30.0,  # 30s for mutating operations
            ),
            LogCostResponse,
        )

    def log_access(
        self, run_id: str, body: LogAccessRequest, jwt: str
    ) -> LogAccessResponse:
        """
        Log access attempt for a run

        Args:
            run_id: Run identifier (required)
            body: Access details
            jwt: JWT token

        Returns:
            LogAccessResponse with ok status

        Raises:
            WearError: If run_id is missing or on API errors
        """
        if not run_id:
            raise WearError("log_access requires run_id", 400, WearErrorResponse(error="missing_run_id"))

        return self._retryable_request(
            "log_access",
            lambda: self._client.post(
                f"{self.base_url}/v1/runs/log-access",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {jwt}",
                    "X-WEAR-Agent-ID": _extract_agent_id_from_jwt(jwt),
                    "X-WEAR-Run-ID": run_id,
                },
                json=asdict(body),
                timeout=30.0,
            ),
            LogAccessResponse,
        )

    def finish_run(
        self,
        run_id: str,
        status: str,
        jwt: str,
        failure_class: Optional[str] = None,
        model_used: Optional[str] = None,
    ) -> FinishRunResponse:
        """
        Finish a run with status

        Best-effort: On repeated 5xx errors, logs warning and returns ok=False
        instead of throwing, so agents don't crash after completing work.

        Args:
            run_id: Run identifier (required)
            status: Run status ('success', 'failed', or 'blocked')
            jwt: JWT token
            failure_class: Optional failure classification
            model_used: Optional model identifier

        Returns:
            FinishRunResponse with ok status

        Raises:
            WearError: If run_id is missing or on 4xx errors
        """
        if not run_id:
            raise WearError("finish_run requires run_id", 400, WearErrorResponse(error="missing_run_id"))

        body = FinishRunRequest(
            run_id=run_id,
            status=status,
            failure_class=failure_class,
            model_used=model_used,
        )

        try:
            return self._retryable_request(
                "finish_run",
                lambda: self._client.post(
                    f"{self.base_url}/v1/runs/finish",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {jwt}",
                        "X-WEAR-Agent-ID": _extract_agent_id_from_jwt(jwt),
                        "X-WEAR-Run-ID": run_id,
                    },
                    json=asdict(body),
                    timeout=30.0,
                ),
                FinishRunResponse,
            )
        except WearError as error:
            # Best-effort: if all retries failed with 5xx, log but don't throw
            if _is_retryable_error(error.status_code):
                logger.warning(f"[WearClient] finish_run failed after retries (best-effort): {error}")
                return FinishRunResponse(ok=False)
            raise

    def _retryable_request(
        self,
        method: str,
        request_fn: Callable[[], httpx.Response],
        response_type: type[T],
    ) -> T:
        """
        Execute a request with retry logic for 5xx errors

        Args:
            method: Method name for error messages
            request_fn: Function that makes the HTTP request
            response_type: Type to construct from response

        Returns:
            Instance of response_type

        Raises:
            WearError: On non-retryable errors or after max retries
        """
        last_error: Optional[WearError] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = request_fn()

                if not response.is_success:
                    error_body = self._parse_error_response(response)
                    error = WearError(
                        self._format_error_message(method, response.status_code, error_body),
                        response.status_code,
                        error_body,
                    )

                    # Don't retry on 4xx errors
                    if not _is_retryable_error(response.status_code):
                        raise error

                    last_error = error

                    # Retry on 5xx
                    if attempt < MAX_RETRIES:
                        delay = _get_backoff_delay(attempt)
                        time.sleep(delay)
                        continue
                else:
                    data = response.json()
                    return response_type(**data)

            except WearError:
                raise
            except Exception as e:
                # Network errors or other failures - retry
                if attempt < MAX_RETRIES:
                    delay = _get_backoff_delay(attempt)
                    time.sleep(delay)
                    continue
                raise WearError(f"{method} failed: {str(e)}", 500, WearErrorResponse())

        # All retries exhausted
        if last_error:
            raise last_error
        raise WearError(f"{method} failed after {MAX_RETRIES} attempts", 500, WearErrorResponse())

    def _format_error_message(
        self,
        method: str,
        status: int,
        error_body: WearErrorResponse,
    ) -> str:
        """Format error message with context"""
        parts = [f"{method} failed: {status}"]

        if error_body.error:
            parts.append(error_body.error)

        if error_body.code:
            parts.append(f"[{error_body.code}]")

        if error_body.reason:
            parts.append(error_body.reason)

        return " - ".join(parts)
