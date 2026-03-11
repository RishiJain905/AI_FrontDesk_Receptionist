"""Pure after-hours gate helpers for runtime entrypoint decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from hvac_types.business_config import BusinessConfig
from utils.time import (
    TimezoneResolutionError,
    get_local_now,
    parse_time_window,
    resolve_timezone,
)


@dataclass(frozen=True)
class GateDecision:
    """Deterministic after-hours decision derived from config + wall clock."""

    is_after_hours: bool
    timezone: str
    local_time: str
    window_start: str
    window_end: str


def _is_within_window(*, current: time, start: time, end: time) -> bool:
    if start == end:
        return True

    if start < end:
        return start <= current < end

    return current >= start or current < end


def _nth_weekday_of_month(*, year: int, month: int, weekday: int, nth: int) -> date:
    month_start = date(year, month, 1)
    day_offset = (weekday - month_start.weekday()) % 7
    day = 1 + day_offset + (nth - 1) * 7
    return date(year, month, day)


def _fallback_toronto_local(utc_now: datetime) -> datetime:
    year = utc_now.year
    dst_start_local = _nth_weekday_of_month(year=year, month=3, weekday=6, nth=2)
    dst_end_local = _nth_weekday_of_month(year=year, month=11, weekday=6, nth=1)

    dst_start_utc = datetime.combine(
        dst_start_local,
        time(7, 0),
        tzinfo=timezone.utc,
    )
    dst_end_utc = datetime.combine(
        dst_end_local,
        time(6, 0),
        tzinfo=timezone.utc,
    )

    offset_hours = -4 if dst_start_utc <= utc_now < dst_end_utc else -5
    offset = timedelta(hours=offset_hours)
    return utc_now.astimezone(timezone(offset, name="America/Toronto"))


def _resolve_local_time(*, timezone_name: str, now: datetime | None) -> datetime:
    if now is None:
        return get_local_now(timezone_name)

    reference_time = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)

    try:
        timezone_info = resolve_timezone(timezone_name)
    except TimezoneResolutionError as exc:
        if timezone_name == "America/Toronto":
            return _fallback_toronto_local(reference_time.astimezone(timezone.utc))
        raise TimezoneResolutionError(str(exc)) from exc

    return reference_time.astimezone(timezone_info)


def is_after_hours(config: BusinessConfig, *, now: datetime | None = None) -> GateDecision:
    """Evaluate whether ``now`` lands inside the configured after-hours window."""

    timezone_name = (config.timezone or "").strip()
    window_start, window_end = parse_time_window(
        config.after_hours_start,
        config.after_hours_end,
    )
    local_now = _resolve_local_time(timezone_name=timezone_name, now=now)

    in_window = _is_within_window(
        current=local_now.time(),
        start=window_start,
        end=window_end,
    )

    return GateDecision(
        is_after_hours=in_window,
        timezone=timezone_name,
        local_time=local_now.strftime("%H:%M"),
        window_start=window_start.strftime("%H:%M"),
        window_end=window_end.strftime("%H:%M"),
    )


__all__ = ["GateDecision", "is_after_hours"]
