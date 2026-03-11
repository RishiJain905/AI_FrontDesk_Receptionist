"""Slot state types for HVAC agent conversation slot-filling.

A "slot" represents a piece of information the agent needs to collect from
the caller (e.g. issue category, name, address). Each slot has a status
that tracks whether the information has been elicited, filled, and confirmed
by the caller.

Note: Python 3.11+ changed str(StrEnum) to return 'ClassName.MEMBER'. We
override __str__ to return the raw value, consistent with classification.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SlotStatus(str, Enum):
    """Current fill-state of a conversation slot.

    State transitions:
        EMPTY → FILLED (LLM extracts a candidate value from transcript)
        FILLED → CONFIRMED (caller or LLM confirms the extracted value)
        FILLED → EMPTY (extracted value rejected; slot cleared for re-ask)
    """

    def __str__(self) -> str:
        return self.value

    EMPTY = "empty"
    FILLED = "filled"
    CONFIRMED = "confirmed"


@dataclass
class SlotState:
    """Mutable state for a single conversation slot.

    Attributes:
        status:     Current fill-state of the slot.
        value:      The extracted or confirmed value; ``None`` when EMPTY.
        confidence: Model confidence [0.0-1.0] for the extracted value;
                    ``None`` when the value was not LLM-extracted.
        attempts:   Number of times the agent has asked for this slot.
                    Used to detect stuck slots and decide when to escalate.
    """

    status: SlotStatus = field(default=SlotStatus.EMPTY)
    value: Any = field(default=None)
    confidence: float | None = field(default=None)
    attempts: int = field(default=0)
