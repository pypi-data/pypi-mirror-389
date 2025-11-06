"""
wear_sdk - Python SDK for WEAR Gateway

Phase 3 SDK with proper headers, error mapping, and type safety.
Uses Pydantic models generated from OpenAPI spec.
"""

from .client import WearClient, WearClientOptions
from .errors import WearError, WearErrorResponse
from .types import StartRunResponse

# Re-export generated models for convenience
from .generated_models import (
    ErrorResponse,
    FinishRunRequest,
    FinishRunResponse,
    HealthResponse,
    StartRunRequest,
    TokenRequest,
    TokenResponse,
)

__version__ = "0.1.0"

__all__ = [
    "WearClient",
    "WearClientOptions",
    "WearError",
    "WearErrorResponse",
    "StartRunResponse",
    # Generated models
    "ErrorResponse",
    "FinishRunRequest",
    "FinishRunResponse",
    "HealthResponse",
    "StartRunRequest",
    "StartRunResponse",
    "TokenRequest",
    "TokenResponse",
]
