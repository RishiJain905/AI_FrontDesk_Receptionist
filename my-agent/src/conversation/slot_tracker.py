"""Deterministic slot tracking for adaptive intake flows.

This module keeps the S01 ``SlotState`` contract intact while exposing the S02
inspection helpers that reason in terms of missing, tentative, and confirmed
slots.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from hvac_types.slot_state import SlotState, SlotStatus


class SlotTracker:
    """Manage mutable slot state with deterministic inspection helpers."""

    def __init__(self, required_slots: list[str] | tuple[str, ...]) -> None:
        self._required_slots = list(dict.fromkeys(required_slots))
        self._slots: dict[str, SlotState] = {
            slot_name: SlotState() for slot_name in self._required_slots
        }

    @property
    def required_slots(self) -> list[str]:
        """Return the required-slot subset in stable order."""

        return list(self._required_slots)

    def register_slot(self, slot_name: str) -> None:
        """Ensure an optional slot exists without changing requirement state."""

        self._slots.setdefault(slot_name, SlotState())

    def record_candidate(
        self,
        slot_name: str,
        value: Any,
        *,
        confidence: float | None = None,
    ) -> SlotState:
        """Record a non-confirmed candidate value for a slot."""

        slot = self._get_or_create_slot(slot_name)
        slot.status = SlotStatus.FILLED
        slot.value = value
        slot.confidence = confidence
        return deepcopy(slot)

    def confirm(self, slot_name: str, value: Any | None = None) -> SlotState:
        """Mark a slot as caller-confirmed.

        If ``value`` is provided, it replaces any previous candidate. When no
        value is provided, the existing candidate is promoted to confirmed.
        """

        slot = self._get_or_create_slot(slot_name)
        if value is not None:
            slot.value = value
            slot.confidence = None
        if slot.value is None:
            msg = f"Cannot confirm slot '{slot_name}' without a value"
            raise ValueError(msg)
        slot.status = SlotStatus.CONFIRMED
        slot.confidence = None
        return deepcopy(slot)

    def reject(self, slot_name: str) -> SlotState:
        """Clear a slot back to the missing state."""

        slot = self._get_or_create_slot(slot_name)
        slot.status = SlotStatus.EMPTY
        slot.value = None
        slot.confidence = None
        return deepcopy(slot)

    def snapshot(self) -> dict[str, SlotState]:
        """Return a detached copy of the full slot state."""

        return {slot_name: deepcopy(state) for slot_name, state in self._slots.items()}

    def get_missing_slots(self) -> list[str]:
        """Return required slots that are still empty."""

        return [
            slot_name
            for slot_name in self._required_slots
            if self._slots[slot_name].status == SlotStatus.EMPTY
        ]

    def get_tentative_slots(self) -> list[str]:
        """Return all slots that hold unconfirmed candidate values."""

        return [
            slot_name
            for slot_name, state in self._slots.items()
            if state.status == SlotStatus.FILLED
        ]

    def all_required_confirmed(self) -> bool:
        """Return whether every required slot is explicitly confirmed."""

        return all(
            self._slots[slot_name].status == SlotStatus.CONFIRMED
            for slot_name in self._required_slots
        )

    def _get_or_create_slot(self, slot_name: str) -> SlotState:
        self.register_slot(slot_name)
        return self._slots[slot_name]
