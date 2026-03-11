"""Deterministic GoHighLevel payload builders for finalized call records."""

from __future__ import annotations

from enum import Enum
from typing import Any

from hvac_types.call_intake_record import CallIntakeRecord
from utils.phone import normalize_phone


def build_contact_payload(
    record: CallIntakeRecord,
    *,
    location_id: str,
) -> dict[str, str]:
    """Map a finalized call record into a GoHighLevel contact payload."""

    payload: dict[str, str] = {"locationId": location_id}

    if record.customer_name:
        payload["firstName"] = record.customer_name

    normalized_phone = normalize_phone(record.phone_number)
    if normalized_phone:
        payload["phone"] = normalized_phone

    if record.service_address:
        payload["address1"] = record.service_address

    return payload


def build_contact_note(record: CallIntakeRecord) -> str:
    """Render deterministic structured note text for the CRM timeline."""

    lines: list[str] = []

    _append_scalar(lines, "Call Status", record.call_status)
    _append_scalar(lines, "Issue Category", record.issue_category)
    _append_scalar(lines, "Urgency Level", record.urgency_level)
    _append_scalar(lines, "Danger Type", record.danger_type)
    _append_scalar(lines, "Customer Type", record.customer_type)
    _append_scalar(lines, "Callback Requested", _yes_no(record.callback_requested))
    _append_scalar(lines, "Callback Time", record.callback_time)
    _append_scalar(lines, "Summary", record.summary)
    _append_block(lines, "Transcript", record.transcript)
    _append_block(lines, "AI Summary", record.ai_summary)

    return "\n".join(lines)


def to_ghl_contact(record: CallIntakeRecord, location_id: str) -> dict[str, str]:
    """Alias kept for slice-plan naming consistency."""

    return build_contact_payload(record, location_id=location_id)


def to_ghl_note(record: CallIntakeRecord) -> str:
    """Alias kept for slice-plan naming consistency."""

    return build_contact_note(record)


def _append_scalar(lines: list[str], label: str, value: Any | None) -> None:
    rendered = _render_value(value)
    if rendered is None:
        return
    lines.append(f"{label}: {rendered}")


def _append_block(lines: list[str], label: str, value: str | None) -> None:
    rendered = _render_value(value)
    if rendered is None:
        return
    lines.append(f"{label}:")
    lines.append(rendered)


def _render_value(value: Any | None) -> str | None:
    if value is None:
        return None

    if isinstance(value, Enum):
        return str(value)

    text = str(value).strip()
    if not text:
        return None
    return text


def _yes_no(value: bool | None) -> str | None:
    if value is None:
        return None
    return "yes" if value else "no"


__all__ = [
    "build_contact_note",
    "build_contact_payload",
    "to_ghl_contact",
    "to_ghl_note",
]
