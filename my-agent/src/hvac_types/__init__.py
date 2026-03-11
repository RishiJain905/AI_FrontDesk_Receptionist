"""HVAC-specific types for conversation state, slot management, and LLM classification."""

from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel
from hvac_types.slot_state import SlotState, SlotStatus

__all__ = [
    "DangerType",
    "IssueCategory",
    "SlotState",
    "SlotStatus",
    "UrgencyLevel",
]
