"""
Unit tests for log_cost, log_access, and finish_run methods

Tests Part B requirements: run_id validation, retries, headers, error mapping
"""

import pytest
from unittest.mock import Mock, patch
import httpx

from wear_sdk import WearClient, WearClientOptions, WearError
from wear_sdk.types import LogCostRequest, LogAccessRequest


class TestWearClientPartB:
    """Tests for Part B methods: log_cost, log_access, finish_run"""

    @pytest.fixture
    def client(self):
        return WearClient(WearClientOptions(base_url="https://test.example.com"))

    @pytest.fixture
    def mock_run_id(self):
        return "123e4567-e89b-12d3-a456-426614174000"

    @pytest.fixture
    def mock_jwt(self):
        return "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhaWQiOiJ0ZXN0LWFnZW50In0.sig"

    # log_cost tests
    def test_log_cost_throws_if_run_id_missing(self, client, mock_jwt):
        """Should throw if run_id is missing"""
        with pytest.raises(WearError) as exc_info:
            client.log_cost("", LogCostRequest(run_id=""), mock_jwt)
        assert "log_cost requires run_id" in str(exc_info.value)

    def test_log_cost_sends_required_headers(self, client, mock_run_id, mock_jwt):
        """Should send required headers including X-WEAR-Run-ID"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = True
        mock_response.json.return_value = {"ok": True, "correlation_id": "corr-123"}

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            client.log_cost(
                mock_run_id,
                LogCostRequest(
                    run_id=mock_run_id,
                    tokens_prompt=100,
                    tokens_output=50,
                    model_cost_cents=10,
                ),
                mock_jwt,
            )

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://test.example.com/v1/runs/log-cost"
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == f"Bearer {mock_jwt}"
            assert headers["X-WEAR-Agent-ID"] == "test-agent"
            assert headers["X-WEAR-Run-ID"] == mock_run_id

    def test_log_cost_no_retry_on_4xx(self, client, mock_run_id, mock_jwt):
        """Should not retry on 4xx errors"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 422
        mock_response.text = '{"error": "invalid_request"}'

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            with pytest.raises(WearError):
                client.log_cost(mock_run_id, LogCostRequest(run_id=mock_run_id), mock_jwt)

            assert mock_post.call_count == 1

    def test_log_cost_retries_on_5xx(self, client, mock_run_id, mock_jwt):
        """Should retry on 5xx errors with exponential backoff"""
        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = Mock(spec=httpx.Response)
            if call_count < 3:
                mock_response.is_success = False
                mock_response.status_code = 503
                mock_response.text = '{"error": "service_unavailable"}'
            else:
                mock_response.is_success = True
                mock_response.json.return_value = {"ok": True}
            return mock_response

        with patch.object(client._client, "post", side_effect=mock_post_fn):
            with patch("time.sleep"):  # Mock sleep to speed up test
                result = client.log_cost(
                    mock_run_id, LogCostRequest(run_id=mock_run_id), mock_jwt
                )

            assert result.ok is True
            assert call_count == 3

    def test_log_cost_throws_after_max_retries(self, client, mock_run_id, mock_jwt):
        """Should throw after max retries on persistent 5xx"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = '{"error": "internal_error"}'

        with patch.object(client._client, "post", return_value=mock_response):
            with patch("time.sleep"):
                with pytest.raises(WearError):
                    client.log_cost(
                        mock_run_id, LogCostRequest(run_id=mock_run_id), mock_jwt
                    )

    # log_access tests
    def test_log_access_throws_if_run_id_missing(self, client, mock_jwt):
        """Should throw if run_id is missing"""
        with pytest.raises(WearError) as exc_info:
            client.log_access(
                "",
                LogAccessRequest(
                    run_id="",
                    resource_type="database",
                    operation="read",
                    purpose="analysis",
                    allowed=True,
                ),
                mock_jwt,
            )
        assert "log_access requires run_id" in str(exc_info.value)

    def test_log_access_sends_required_headers(self, client, mock_run_id, mock_jwt):
        """Should send required headers including X-WEAR-Run-ID"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = True
        mock_response.json.return_value = {"ok": True, "correlation_id": "corr-456"}

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            client.log_access(
                mock_run_id,
                LogAccessRequest(
                    run_id=mock_run_id,
                    resource_type="database",
                    operation="read",
                    purpose="analysis",
                    allowed=True,
                    pii_score=0.5,
                ),
                mock_jwt,
            )

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://test.example.com/v1/runs/log-access"
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == f"Bearer {mock_jwt}"
            assert headers["X-WEAR-Agent-ID"] == "test-agent"
            assert headers["X-WEAR-Run-ID"] == mock_run_id

    def test_log_access_logs_denied_attempts(self, client, mock_run_id, mock_jwt):
        """Should log denied access attempts (allowed=False)"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = True
        mock_response.json.return_value = {"ok": True}

        with patch.object(client._client, "post", return_value=mock_response):
            result = client.log_access(
                mock_run_id,
                LogAccessRequest(
                    run_id=mock_run_id,
                    resource_type="pii_data",
                    operation="write",
                    purpose="testing",
                    allowed=False,
                ),
                mock_jwt,
            )

            assert result.ok is True

    def test_log_access_retries_on_5xx(self, client, mock_run_id, mock_jwt):
        """Should retry on 5xx errors"""
        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = Mock(spec=httpx.Response)
            if call_count == 1:
                mock_response.is_success = False
                mock_response.status_code = 502
                mock_response.text = '{"error": "bad_gateway"}'
            else:
                mock_response.is_success = True
                mock_response.json.return_value = {"ok": True}
            return mock_response

        with patch.object(client._client, "post", side_effect=mock_post_fn):
            with patch("time.sleep"):
                result = client.log_access(
                    mock_run_id,
                    LogAccessRequest(
                        run_id=mock_run_id,
                        resource_type="api",
                        operation="call",
                        purpose="integration",
                        allowed=True,
                    ),
                    mock_jwt,
                )

            assert result.ok is True
            assert call_count == 2

    # finish_run tests
    def test_finish_run_throws_if_run_id_missing(self, client, mock_jwt):
        """Should throw if run_id is missing"""
        with pytest.raises(WearError) as exc_info:
            client.finish_run("", "success", mock_jwt)
        assert "finish_run requires run_id" in str(exc_info.value)

    def test_finish_run_sends_required_headers(self, client, mock_run_id, mock_jwt):
        """Should send required headers including X-WEAR-Run-ID"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = True
        mock_response.json.return_value = {"ok": True, "correlation_id": "corr-789"}

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            client.finish_run(mock_run_id, "success", mock_jwt, model_used="gpt-4")

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://test.example.com/v1/runs/finish"
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == f"Bearer {mock_jwt}"
            assert headers["X-WEAR-Agent-ID"] == "test-agent"
            assert headers["X-WEAR-Run-ID"] == mock_run_id
            assert call_args[1]["json"]["status"] == "success"
            assert call_args[1]["json"]["model_used"] == "gpt-4"

    def test_finish_run_supports_all_status_values(self, client, mock_run_id, mock_jwt):
        """Should support all status values"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = True
        mock_response.json.return_value = {"ok": True}

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            client.finish_run(mock_run_id, "success", mock_jwt)
            client.finish_run(mock_run_id, "failed", mock_jwt, failure_class="timeout")
            client.finish_run(mock_run_id, "blocked", mock_jwt)

            assert mock_post.call_count == 3

    def test_finish_run_best_effort_on_persistent_5xx(self, client, mock_run_id, mock_jwt):
        """Should be best-effort: return ok=False on persistent 5xx instead of throwing"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 503
        mock_response.text = '{"error": "service_unavailable"}'

        with patch.object(client._client, "post", return_value=mock_response):
            with patch("time.sleep"):
                with patch("wear_sdk.client.logger.warning") as mock_warning:
                    result = client.finish_run(mock_run_id, "success", mock_jwt)

                    assert result.ok is False
                    mock_warning.assert_called_once()

    def test_finish_run_throws_on_4xx(self, client, mock_run_id, mock_jwt):
        """Should throw on 4xx errors (not best-effort for client errors)"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 409
        mock_response.text = '{"error": "conflict"}'

        with patch.object(client._client, "post", return_value=mock_response):
            with pytest.raises(WearError):
                client.finish_run(mock_run_id, "success", mock_jwt)

    # Error mapping tests
    def test_error_mapping_401(self, client, mock_run_id, mock_jwt):
        """Should map 401 unauthorized"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.text = '{"error": "unauthorized"}'

        with patch.object(client._client, "post", return_value=mock_response):
            with pytest.raises(WearError) as exc_info:
                client.log_cost(mock_run_id, LogCostRequest(run_id=mock_run_id), mock_jwt)

            assert exc_info.value.status_code == 401

    def test_error_mapping_403_policy_denial(self, client, mock_run_id, mock_jwt):
        """Should map 403 policy denial"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 403
        mock_response.text = '{"code": "policy_denied", "reason": "Insufficient permissions", "rule_id": "rule_010"}'

        with patch.object(client._client, "post", return_value=mock_response):
            with pytest.raises(WearError) as exc_info:
                client.log_access(
                    mock_run_id,
                    LogAccessRequest(
                        run_id=mock_run_id,
                        resource_type="sensitive",
                        operation="delete",
                        purpose="cleanup",
                        allowed=False,
                    ),
                    mock_jwt,
                )

            error = exc_info.value
            assert error.status_code == 403
            assert error.is_policy_denied() is True
            assert error.error_response.rule_id == "rule_010"

    def test_error_mapping_422_validation(self, client, mock_run_id, mock_jwt):
        """Should map 422 validation error"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 422
        mock_response.text = '{"error": "validation_error", "reason": "Invalid cost value"}'

        with patch.object(client._client, "post", return_value=mock_response):
            with pytest.raises(WearError) as exc_info:
                client.log_cost(
                    mock_run_id,
                    LogCostRequest(run_id=mock_run_id, model_cost_cents=-1),
                    mock_jwt,
                )

            assert exc_info.value.status_code == 422
