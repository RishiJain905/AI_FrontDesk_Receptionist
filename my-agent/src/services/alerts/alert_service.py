"""Provider-agnostic alert protocol for finalized call records."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from hvac_types.call_intake_record import CallIntakeRecord


@runtime_checkable
class AlertService(Protocol):
    """Async contract for owner alert providers used during finalization."""

    async def send_owner_sms(self, record: CallIntakeRecord) -> bool:
        """Send the owner alert if needed and return whether an SMS was sent."""
