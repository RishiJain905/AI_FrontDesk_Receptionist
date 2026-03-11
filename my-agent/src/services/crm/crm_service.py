"""Provider-agnostic CRM protocol for finalized call records."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from hvac_types.call_intake_record import CallIntakeRecord


@runtime_checkable
class CrmService(Protocol):
    """Async contract for CRM providers used during call finalization."""

    async def upsert_contact(self, record: CallIntakeRecord) -> str:
        """Create or update a CRM contact and return the downstream contact id."""

    async def attach_call_note(self, contact_id: str, note_body: str) -> str | None:
        """Attach a finalized call note to an existing CRM contact."""
