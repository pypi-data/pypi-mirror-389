"""
AgentBill Python SDK
OpenTelemetry-based SDK for tracking AI agent usage and billing
"""

from .client import AgentBill
from .tracer import AgentBillTracer
from .types import AgentBillConfig, TraceContext
from .validation import (
    validate_api_key,
    validate_base_url,
    validate_customer_id,
    validate_event_name,
    validate_metadata,
    validate_revenue,
    ValidationError
)

__version__ = "5.0.0"
__all__ = [
    "AgentBill", 
    "AgentBillTracer", 
    "AgentBillConfig", 
    "TraceContext",
    "ValidationError",
    "validate_api_key",
    "validate_base_url",
    "validate_customer_id",
    "validate_event_name",
    "validate_metadata",
    "validate_revenue"
]
