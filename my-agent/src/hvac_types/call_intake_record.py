"""Finalized call intake record model for CRM/SMS downstream systems."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel


class CallStatus(str, Enum):
    """Completion state for finalized intake records."""

    PARTIAL = "partial"
    COMPLETE = "complete"

    def __str__(self) -> str:
        return self.value


@dataclass
class CallIntakeRecord:
    """Resolved intake record persisted after call completion or fallback."""

    call_status: CallStatus | None = None
    customer_name: str | None = None
    phone_number: str | None = None
    service_address: str | None = None

    issue_category: IssueCategory | None = None
    urgency_level: UrgencyLevel | None = None
    danger_type: DangerType | None = None

    has_pets: bool | None = None
    is_someone_home: bool | None = None
    callback_requested: bool | None = None

    summary: str | None = None
    notes: str | None = None
