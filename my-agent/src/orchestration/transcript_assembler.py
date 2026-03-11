"""Committed conversation transcript assembly for call finalization."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_NOISE_ONLY_PATTERN = re.compile(r"^[^A-Za-z0-9]+$")


@dataclass(frozen=True)
class TranscriptLine:
    """One committed transcript line captured from the runtime session."""

    role: str
    text: str

    def render(self) -> str:
        return f"{self.role}: {self.text}"


class TranscriptAssembler:
    """Build an ordered transcript from committed ``conversation_item_added`` events."""

    def __init__(self) -> None:
        self._lines: list[TranscriptLine] = []

    def add_event(self, payload: Any) -> bool:
        """Capture one transcript line from an event payload.

        Returns ``True`` when an item was accepted and appended.
        """

        item = _extract_item(payload)
        if item is None:
            return False

        if getattr(item, "type", "message") != "message":
            return False
        if bool(getattr(item, "interrupted", False)):
            return False

        role = _normalize_role(getattr(item, "role", None))
        if role is None:
            return False

        text = _extract_text(item)
        if text is None:
            return False

        self._lines.append(TranscriptLine(role=role, text=text))
        return True

    @property
    def line_count(self) -> int:
        return len(self._lines)

    def render(self) -> str:
        if not self._lines:
            return ""
        return "\n".join(line.render() for line in self._lines)

    def lines(self) -> tuple[TranscriptLine, ...]:
        return tuple(self._lines)


def _extract_item(payload: Any) -> Any | None:
    if payload is None:
        return None

    if hasattr(payload, "item"):
        return getattr(payload, "item")

    return payload


def _normalize_role(raw_role: Any) -> str | None:
    if not isinstance(raw_role, str):
        return None

    normalized = raw_role.strip().casefold()
    if normalized not in {"assistant", "user"}:
        return None

    return normalized


def _extract_text(item: Any) -> str | None:
    raw_text = getattr(item, "text_content", None)
    if raw_text is None and hasattr(item, "text"):
        raw_text = getattr(item, "text")

    if not isinstance(raw_text, str):
        return None

    text = " ".join(raw_text.split()).strip()
    if not text:
        return None
    if _NOISE_ONLY_PATTERN.fullmatch(text):
        return None

    return text


__all__ = ["TranscriptAssembler", "TranscriptLine"]
