"""
Type definitions for WEAR SDK responses

Note: Will be replaced by Pydantic models generated from OpenAPI spec
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class StartRunResponse:
    """Response from start_run()"""
    run_id: str
    started_at: str
    correlation_id: Optional[str] = None


@dataclass
class LogCostRequest:
    """Request body for log_cost()"""
    run_id: str
    tokens_prompt: Optional[int] = None
    tokens_output: Optional[int] = None
    model_cost_cents: Optional[int] = None
    tool_cost_cents: Optional[int] = None
    infra_cost_cents: Optional[int] = None


@dataclass
class LogCostResponse:
    """Response from log_cost()"""
    ok: bool
    correlation_id: Optional[str] = None


@dataclass
class LogAccessRequest:
    """Request body for log_access()"""
    run_id: str
    resource_type: str
    operation: str
    purpose: str
    allowed: bool
    resource_id: Optional[str] = None
    fields: Optional[List[str]] = None
    pii_score: Optional[float] = None


@dataclass
class LogAccessResponse:
    """Response from log_access()"""
    ok: bool
    correlation_id: Optional[str] = None


@dataclass
class FinishRunRequest:
    """Request body for finish_run()"""
    run_id: str
    status: str  # 'success', 'failed', or 'blocked'
    failure_class: Optional[str] = None
    model_used: Optional[str] = None


@dataclass
class FinishRunResponse:
    """Response from finish_run()"""
    ok: bool
    correlation_id: Optional[str] = None
