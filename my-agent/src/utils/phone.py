"""Phone normalization helpers shared across CRM and SMS integrations."""

from __future__ import annotations

import re

_DIGIT_PATTERN = re.compile(r"\D+")


def normalize_phone(number: str | None) -> str | None:
    """Return an E.164 North American phone number or ``None`` if unusable.

    The intake flow currently emits North American numbers only. This helper
    accepts the common local formats used throughout the tests and normalizes
    them to ``+1XXXXXXXXXX`` for downstream CRM matching and SMS sending.
    """

    if number is None:
        return None

    stripped = number.strip()
    if not stripped:
        return None

    digits = _DIGIT_PATTERN.sub("", stripped)
    if len(digits) == 10:
        return f"+1{digits}"

    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"

    return None
