from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hvac_types.business_config import BusinessConfig
from orchestration.after_hours_gate import GateDecision, is_after_hours
from utils.time import TimezoneResolutionError, resolve_timezone


def _config(*, start: str, end: str, tz: str = "America/Toronto") -> BusinessConfig:
    return BusinessConfig(
        business_name="North Star HVAC",
        owner_phone="+1-416-555-0110",
        timezone=tz,
        after_hours_start=start,
        after_hours_end=end,
    )


@pytest.mark.parametrize(
    ("utc_now", "expected"),
    [
        (datetime(2026, 1, 15, 17, 30, tzinfo=timezone.utc), True),  # 12:30 Toronto
        (datetime(2026, 1, 15, 16, 30, tzinfo=timezone.utc), False),  # 11:30 Toronto
        (datetime(2026, 1, 15, 22, 0, tzinfo=timezone.utc), False),  # 17:00 Toronto
    ],
)
def test_is_after_hours_handles_same_day_windows(utc_now: datetime, expected: bool) -> None:
    decision = is_after_hours(
        _config(start="12:00", end="17:00"),
        now=utc_now,
    )

    assert isinstance(decision, GateDecision)
    assert decision.is_after_hours is expected
    assert decision.timezone == "America/Toronto"


@pytest.mark.parametrize(
    ("utc_now", "expected"),
    [
        (datetime(2026, 1, 16, 4, 30, tzinfo=timezone.utc), True),  # 23:30 Toronto
        (datetime(2026, 1, 16, 13, 59, tzinfo=timezone.utc), True),  # 08:59 Toronto
        (datetime(2026, 1, 16, 14, 0, tzinfo=timezone.utc), False),  # 09:00 Toronto
        (datetime(2026, 1, 16, 21, 59, tzinfo=timezone.utc), False),  # 16:59 Toronto
        (datetime(2026, 1, 16, 22, 0, tzinfo=timezone.utc), True),  # 17:00 Toronto
    ],
)
def test_is_after_hours_handles_overnight_windows_crossing_midnight(
    utc_now: datetime,
    expected: bool,
) -> None:
    decision = is_after_hours(
        _config(start="17:00", end="09:00"),
        now=utc_now,
    )

    assert decision.is_after_hours is expected


def test_is_after_hours_supports_injectable_now_without_touching_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _clock_should_not_run(*_args, **_kwargs):
        raise AssertionError("expected is_after_hours(..., now=...) to bypass runtime clock lookup")

    monkeypatch.setattr("orchestration.after_hours_gate.get_local_now", _clock_should_not_run)

    decision = is_after_hours(
        _config(start="17:00", end="09:00"),
        now=datetime(2026, 1, 16, 4, 30, tzinfo=timezone.utc),
    )

    assert decision.is_after_hours is True


def test_invalid_or_missing_timezone_raises_typed_resolution_error() -> None:
    with pytest.raises(TimezoneResolutionError, match="America/Nope"):
        resolve_timezone("America/Nope")

    with pytest.raises(TimezoneResolutionError, match="timezone"):
        is_after_hours(_config(start="17:00", end="09:00", tz=""))
