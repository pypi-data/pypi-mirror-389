"""
Unit tests for wear_sdk

Tests success scenarios and policy/budget denial error mapping
"""

import json
from unittest.mock import Mock, patch

import httpx
import pytest

from wear_sdk import WearClient, WearClientOptions, WearError
from wear_sdk.types import StartRunResponse


@pytest.fixture
def client() -> WearClient:
    """Create a test client"""
    return WearClient(WearClientOptions(base_url="https://test.example.com"))


@pytest.fixture
def mock_agent_id() -> str:
    return "test-agent-1"


@pytest.fixture
def mock_jwt() -> str:
    return "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.test.sig"


class TestWearClient:
    """Tests for WearClient"""

    def test_start_run_success(
        self, client: WearClient, mock_agent_id: str, mock_jwt: str
    ) -> None:
        """Should successfully start a run with required headers"""
        mock_response = {
            "run_id": "123e4567-e89b-12d3-a456-426614174000",
            "started_at": "2025-11-03T12:00:00.000Z",
            "correlation_id": "corr-123",
        }

        with patch.object(client._client, "post") as mock_post:
            mock_post.return_value = Mock(
                is_success=True,
                json=lambda: mock_response,
            )

            result = client.start_run(mock_agent_id, mock_jwt)

            assert isinstance(result, StartRunResponse)
            assert result.run_id == mock_response["run_id"]
            assert result.started_at == mock_response["started_at"]
            assert result.correlation_id == mock_response["correlation_id"]

            # Verify headers
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["headers"]["Authorization"] == f"Bearer {mock_jwt}"
            assert call_kwargs["headers"]["X-WEAR-Agent-ID"] == mock_agent_id
            assert call_kwargs["json"]["agent_id"] == mock_agent_id

    def test_start_run_policy_denial(
        self, client: WearClient, mock_agent_id: str, mock_jwt: str
    ) -> None:
        """Should handle policy denial (403 with code)"""
        mock_error_response = {
            "status": 403,
            "code": "policy_denied",
            "reason": "Agent tier insufficient for production access",
            "rule_id": "rule_008",
            "correlation_id": "corr-456",
        }

        with patch.object(client._client, "post") as mock_post:
            mock_post.return_value = Mock(
                is_success=False,
                status_code=403,
                text=json.dumps(mock_error_response),
            )

            with pytest.raises(WearError) as exc_info:
                client.start_run(mock_agent_id, mock_jwt)

            error = exc_info.value
            assert error.status_code == 403
            assert error.is_policy_denied()
            assert not error.is_budget_denied()
            assert error.get_denial_reason() == "Agent tier insufficient for production access"
            assert error.error_response.code == "policy_denied"
            assert error.error_response.rule_id == "rule_008"
            assert "policy_denied" in str(error)
            assert "Agent tier insufficient" in str(error)

    def test_start_run_budget_denial(
        self, client: WearClient, mock_agent_id: str, mock_jwt: str
    ) -> None:
        """Should handle budget denial (403 with budget_exceeded)"""
        mock_error_response = {
            "error": "budget_exceeded",
            "reason": "Monthly budget limit reached (100%)",
            "usage": {
                "tokens_used": 1000000,
                "token_cap": 1000000,
                "cost_used_cents": 10000,
                "cost_cap_cents": 10000,
            },
            "correlation_id": "corr-789",
        }

        with patch.object(client._client, "post") as mock_post:
            mock_post.return_value = Mock(
                is_success=False,
                status_code=403,
                text=json.dumps(mock_error_response),
            )

            with pytest.raises(WearError) as exc_info:
                client.start_run(mock_agent_id, mock_jwt)

            error = exc_info.value
            assert error.status_code == 403
            assert error.is_budget_denied()
            assert not error.is_policy_denied()
            assert error.get_denial_reason() == "Monthly budget limit reached (100%)"
            assert error.error_response.error == "budget_exceeded"
            assert "budget_exceeded" in str(error)

    def test_start_run_agent_not_found(
        self, client: WearClient, mock_agent_id: str, mock_jwt: str
    ) -> None:
        """Should handle 404 agent not found"""
        mock_error_response = {
            "error": "agent_not_found",
            "correlation_id": "corr-404",
        }

        with patch.object(client._client, "post") as mock_post:
            mock_post.return_value = Mock(
                is_success=False,
                status_code=404,
                text=json.dumps(mock_error_response),
            )

            with pytest.raises(WearError) as exc_info:
                client.start_run(mock_agent_id, mock_jwt)

            error = exc_info.value
            assert error.status_code == 404
            assert error.error_response.error == "agent_not_found"

    def test_start_run_internal_error(
        self, client: WearClient, mock_agent_id: str, mock_jwt: str
    ) -> None:
        """Should handle 500 internal error"""
        mock_error_response = {
            "error": "internal_error",
            "correlation_id": "corr-500",
        }

        with patch.object(client._client, "post") as mock_post:
            mock_post.return_value = Mock(
                is_success=False,
                status_code=500,
                text=json.dumps(mock_error_response),
            )

            with pytest.raises(WearError) as exc_info:
                client.start_run(mock_agent_id, mock_jwt)

            error = exc_info.value
            assert error.status_code == 500
            assert error.error_response.error == "internal_error"

    def test_start_run_empty_error_response(
        self, client: WearClient, mock_agent_id: str, mock_jwt: str
    ) -> None:
        """Should handle empty error response body"""
        with patch.object(client._client, "post") as mock_post:
            mock_post.return_value = Mock(
                is_success=False,
                status_code=503,
                text="",
            )

            with pytest.raises(WearError) as exc_info:
                client.start_run(mock_agent_id, mock_jwt)

            error = exc_info.value
            assert error.status_code == 503
            assert error.error_response.error is None

    def test_start_run_malformed_json_response(
        self, client: WearClient, mock_agent_id: str, mock_jwt: str
    ) -> None:
        """Should handle malformed JSON error response"""
        with patch.object(client._client, "post") as mock_post:
            mock_post.return_value = Mock(
                is_success=False,
                status_code=502,
                text="Bad Gateway",
            )

            with pytest.raises(WearError) as exc_info:
                client.start_run(mock_agent_id, mock_jwt)

            error = exc_info.value
            assert error.status_code == 502
            assert error.error_response.error is None

    def test_base_url_trailing_slash_stripped(self) -> None:
        """Should strip trailing slash from base_url"""
        client = WearClient(WearClientOptions(base_url="https://test.example.com/"))
        assert client.base_url == "https://test.example.com"

    def test_context_manager(self) -> None:
        """Should work as context manager"""
        with WearClient(WearClientOptions(base_url="https://test.example.com")) as client:
            assert client is not None
        # Client should be closed after exiting context


class TestWearErrorHelpers:
    """Tests for WearError helper methods"""

    def test_is_policy_denied_true(self) -> None:
        """is_policy_denied should return True for policy denial"""
        from wear_sdk.errors import WearErrorResponse

        error = WearError("test", 403, WearErrorResponse(code="policy_denied"))
        assert error.is_policy_denied()

    def test_is_policy_denied_false_non_403(self) -> None:
        """is_policy_denied should return False for non-403"""
        from wear_sdk.errors import WearErrorResponse

        error = WearError("test", 500, WearErrorResponse(code="policy_denied"))
        assert not error.is_policy_denied()

    def test_is_policy_denied_false_without_code(self) -> None:
        """is_policy_denied should return False without code"""
        from wear_sdk.errors import WearErrorResponse

        error = WearError("test", 403, WearErrorResponse(error="budget_exceeded"))
        assert not error.is_policy_denied()

    def test_is_budget_denied_true(self) -> None:
        """is_budget_denied should return True for budget denial"""
        from wear_sdk.errors import WearErrorResponse

        error = WearError("test", 403, WearErrorResponse(error="budget_exceeded"))
        assert error.is_budget_denied()

    def test_is_budget_denied_false_non_403(self) -> None:
        """is_budget_denied should return False for non-403"""
        from wear_sdk.errors import WearErrorResponse

        error = WearError("test", 500, WearErrorResponse(error="budget_exceeded"))
        assert not error.is_budget_denied()

    def test_get_denial_reason_present(self) -> None:
        """get_denial_reason should return reason when present"""
        from wear_sdk.errors import WearErrorResponse

        error = WearError("test", 403, WearErrorResponse(reason="Test reason"))
        assert error.get_denial_reason() == "Test reason"

    def test_get_denial_reason_absent(self) -> None:
        """get_denial_reason should return None when absent"""
        from wear_sdk.errors import WearErrorResponse

        error = WearError("test", 403, WearErrorResponse())
        assert error.get_denial_reason() is None
