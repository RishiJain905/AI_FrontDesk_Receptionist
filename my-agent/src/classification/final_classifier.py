"""Final classification surface used during call finalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from hvac_types.call_intake_record import CallStatus
from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel
from orchestration.summary_builder import build_ai_summary, build_final_summary


@dataclass(frozen=True)
class FinalClassification:
    """Stable finalization classification result."""

    issue_category: IssueCategory
    urgency_level: UrgencyLevel
    danger_type: DangerType
    summary: str
    ai_summary: str
    notify_owner: bool


class FinalClassifierProtocol(Protocol):
    """Typed protocol for injected final classifiers used by lifecycle tests/runtime."""

    def classify(
        self,
        *,
        controller: Any,
        transcript: str,
        call_status: CallStatus,
    ) -> FinalClassification: ...


class FinalClassifier:
    """Derive final call classification from controller state + committed transcript."""

    def classify(
        self,
        *,
        controller: Any,
        transcript: str,
        call_status: CallStatus,
    ) -> FinalClassification:
        latest = getattr(controller, "latest_classification", None)
        intake_summary = getattr(controller, "last_completed_intake_summary", None)

        issue_category = _coerce_issue_category(getattr(latest, "issue_category", None))
        urgency_level = _coerce_urgency_level(getattr(latest, "urgency_level", None))
        danger_type = _coerce_danger_type(getattr(latest, "danger_type", None))

        summary = build_final_summary(
            call_status=call_status,
            issue_category=issue_category,
            urgency_level=urgency_level,
            danger_type=danger_type,
            intake_summary=intake_summary,
            transcript=transcript,
        )
        ai_summary = build_ai_summary(
            call_status=call_status,
            intake_summary=intake_summary,
            transcript=transcript,
        )

        notify_owner = _should_notify_owner(
            call_status=call_status,
            urgency_level=urgency_level,
            danger_type=danger_type,
            has_handoff=getattr(controller, "handoff_state", None) is not None,
        )

        return FinalClassification(
            issue_category=issue_category,
            urgency_level=urgency_level,
            danger_type=danger_type,
            summary=summary,
            ai_summary=ai_summary,
            notify_owner=notify_owner,
        )


def _coerce_issue_category(value: Any) -> IssueCategory:
    if isinstance(value, IssueCategory):
        return value
    return IssueCategory.OTHER


def _coerce_urgency_level(value: Any) -> UrgencyLevel:
    if isinstance(value, UrgencyLevel):
        return value
    return UrgencyLevel.UNKNOWN


def _coerce_danger_type(value: Any) -> DangerType:
    if isinstance(value, DangerType):
        return value
    return DangerType.NONE


def _should_notify_owner(
    *,
    call_status: CallStatus,
    urgency_level: UrgencyLevel,
    danger_type: DangerType,
    has_handoff: bool,
) -> bool:
    if danger_type != DangerType.NONE or has_handoff:
        return True
    if urgency_level in {UrgencyLevel.URGENT, UrgencyLevel.EMERGENCY}:
        return True
    if call_status == CallStatus.PARTIAL:
        return True
    return False


__all__ = ["FinalClassification", "FinalClassifier", "FinalClassifierProtocol"]
