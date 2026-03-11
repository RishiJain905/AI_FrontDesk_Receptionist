from __future__ import annotations

import pytest

from utils.phone import normalize_phone


@pytest.mark.parametrize(
    ("raw_number", "expected"),
    [
        ("4165550199", "+14165550199"),
        ("416-555-0199", "+14165550199"),
        ("416 555 0199", "+14165550199"),
        ("1-416-555-0199", "+14165550199"),
        ("+14165550199", "+14165550199"),
    ],
)
def test_normalize_phone_returns_e164_for_supported_north_american_formats(
    raw_number: str,
    expected: str,
) -> None:
    assert normalize_phone(raw_number) == expected


@pytest.mark.parametrize(
    "raw_number",
    [None, "", "   ", "5550199", "416-555-019", "abc", "+442071838750"],
)
def test_normalize_phone_returns_none_for_blank_or_invalid_inputs(
    raw_number: str | None,
) -> None:
    assert normalize_phone(raw_number) is None
