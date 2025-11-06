"""
Generated Pydantic models from OpenAPI spec

Note: Currently hand-crafted as OpenAPI spec is minimal.
When OpenAPI spec is expanded with full schemas, regenerate with:
  datamodel-codegen --input docs/tech/openapi.yaml --output wear_sdk/generated_models.py
"""

from typing import Optional

from pydantic import BaseModel, Field


class StartRunRequest(BaseModel):
    """Request body for POST /v1/runs/start"""

    agent_id: str = Field(..., description="Agent identifier")


class StartRunResponse(BaseModel):
    """Response from POST /v1/runs/start"""

    run_id: str = Field(..., description="Unique run identifier (UUID)")
    started_at: str = Field(..., description="ISO 8601 timestamp when run started")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")


class FinishRunRequest(BaseModel):
    """Request body for POST /v1/runs/finish"""

    run_id: str = Field(..., description="Run identifier (UUID)")
    status: str = Field(..., description="Run status: succeeded or failed")
    tokens_used: int = Field(0, ge=0, description="Number of tokens used")
    cost_used_cents: int = Field(0, ge=0, description="Cost in cents")


class FinishRunResponse(BaseModel):
    """Response from POST /v1/runs/finish"""

    ok: bool = Field(..., description="Success indicator")


class TokenRequest(BaseModel):
    """Request body for POST /v1/agents/token"""

    agent_id: str = Field(..., description="Agent identifier")


class TokenResponse(BaseModel):
    """Response from POST /v1/agents/token"""

    token: str = Field(..., description="JWT token")
    expires_at: str = Field(..., description="ISO 8601 expiration timestamp")


class HealthResponse(BaseModel):
    """Response from GET /v1/healthz"""

    status: str = Field(..., description="Health status")
    version: Optional[str] = Field(None, description="API version")
    build: Optional[str] = Field(None, description="Build SHA")
    time: Optional[str] = Field(None, description="Current server time")


class ErrorResponse(BaseModel):
    """Generic error response"""

    error: Optional[str] = Field(None, description="Error code")
    code: Optional[str] = Field(None, description="Policy/budget code")
    reason: Optional[str] = Field(None, description="Human-readable reason")
    rule_id: Optional[str] = Field(None, description="Policy rule identifier")
    status: Optional[int] = Field(None, description="HTTP status code")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
