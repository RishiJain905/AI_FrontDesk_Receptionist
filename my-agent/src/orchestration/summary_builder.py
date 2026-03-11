"""Deterministic final-call summary builders."""

from __future__ import annotations

from typing import Any

from hvac_types.call_intake_record import CallStatus
from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel


def build_final_summary(
    *,
    call_status: CallStatus,
    issue_category: IssueCategory,
    urgency_level: UrgencyLevel,
    danger_type: DangerType,
    intake_summary: Any | None,
    transcript: str,
) -> str:
    """Build a concise deterministic summary for CRM + owner alert surfaces."""

    parts: list[str] = [
        "Completed after-hours intake"
        if call_status == CallStatus.COMPLETE
        else "Partial after-hours intake"
    ]

    caller_name = _slot_value(intake_summary, "customer_name")
    if caller_name:
        parts.append(f"caller={caller_name}")

    if issue_category != IssueCategory.OTHER:
        parts.append(f"issue={issue_category.value}")

    if urgency_level != UrgencyLevel.UNKNOWN:
        parts.append(f"urgency={urgency_level.value}")

    if danger_type != DangerType.NONE:
        parts.append(f"danger={danger_type.value}")

    quote = _transcript_quote(transcript)
    if quote:
        parts.append(f"quote={quote}")

    return "; ".join(parts)


def build_ai_summary(
    *,
    call_status: CallStatus,
    intake_summary: Any | None,
    transcript: str,
) -> str:
    """Build an inspectable machine-oriented summary string."""

    missing_required_slots = _missing_required_slots(intake_summary)
    transcript_excerpt = _transcript_quote(transcript, max_len=220)

    return (
        f"status={call_status.value}; "
        f"missing_required_slots={','.join(missing_required_slots) or '<none>'}; "
        f"transcript_excerpt={transcript_excerpt or '<none>'}"
    )


def _slot_value(intake_summary: Any | None, slot_name: str) -> str | None:
    if intake_summary is None:
        return None

    slots = getattr(intake_summary, "slots", None)
    if not isinstance(slots, dict):
        return None

    state = slots.get(slot_name)
    if state is None:
        return None

    value = getattr(state, "value", None)
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _missing_required_slots(intake_summary: Any | None) -> tuple[str, ...]:
    if intake_summary is None:
        return ()

    missing = getattr(intake_summary, "missing_required_slots", ())
    if not isinstance(missing, tuple):
        return ()
    return tuple(str(item) for item in missing)


def _transcript_quote(transcript: str, *, max_len: int = 120) -> str | None:
    text = " ".join(transcript.split()).strip()
    if not text:
        return None

    if len(text) > max_len:
        text = f"{text[:max_len].rstrip()}…"
    return text


__all__ = ["build_ai_summary", "build_final_summary"]
