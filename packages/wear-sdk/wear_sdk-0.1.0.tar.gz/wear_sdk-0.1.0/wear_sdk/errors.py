"""
Error types for WEAR SDK
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class WearErrorResponse:
    """Error response from Gateway with policy/budget denial details"""

    error: Optional[str] = None
    code: Optional[str] = None
    reason: Optional[str] = None
    rule_id: Optional[str] = None
    status: Optional[int] = None
    correlation_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WearErrorResponse":
        """Create from dictionary"""
        return cls(
            error=data.get("error"),
            code=data.get("code"),
            reason=data.get("reason"),
            rule_id=data.get("rule_id"),
            status=data.get("status"),
            correlation_id=data.get("correlation_id"),
        )


class WearError(Exception):
    """Custom exception for WEAR API errors"""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_response: Optional[WearErrorResponse] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_response = error_response or WearErrorResponse()

    def is_policy_denied(self) -> bool:
        """Returns True if this is a policy denial (403 with code)"""
        return self.status_code == 403 and self.error_response.code is not None

    def is_budget_denied(self) -> bool:
        """Returns True if this is a budget denial"""
        return self.status_code == 403 and self.error_response.error == "budget_exceeded"

    def get_denial_reason(self) -> Optional[str]:
        """Returns the denial reason if available"""
        return self.error_response.reason
