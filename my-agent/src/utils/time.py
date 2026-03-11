"""Timezone and time-window helpers shared by runtime gate orchestration."""

from __future__ import annotations

import re
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_TIME_OF_DAY_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class TimezoneResolutionError(ValueError):
    """Raised when a configured timezone cannot be resolved safely."""


def resolve_timezone(timezone_name: str | None) -> ZoneInfo:
    """Resolve an IANA timezone or raise a clear typed configuration error."""

    if not isinstance(timezone_name, str) or not timezone_name.strip():
        raise TimezoneResolutionError(
            "Invalid BusinessConfig timezone: expected a non-empty IANA timezone string."
        )

    normalized_name = timezone_name.strip()
    try:
        return ZoneInfo(normalized_name)
    except ZoneInfoNotFoundError as exc:
        raise TimezoneResolutionError(
            "Unable to resolve timezone "
            f"{normalized_name!r}. Use a valid IANA timezone (for example "
            "'America/Toronto'). On Windows-like environments without system "
            "zoneinfo data, install the 'tzdata' package."
        ) from exc


def parse_time_of_day(raw_value: str | None, *, field_name: str) -> time:
    """Parse strict HH:MM 24-hour values into ``datetime.time``."""

    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError(
            f"Invalid BusinessConfig: field '{field_name}' must be a non-empty HH:MM string."
        )

    normalized_value = raw_value.strip()
    if not _TIME_OF_DAY_PATTERN.fullmatch(normalized_value):
        raise ValueError(
            f"Invalid BusinessConfig: field '{field_name}' must use HH:MM 24-hour format."
        )

    hours, minutes = normalized_value.split(":", maxsplit=1)
    return time(hour=int(hours), minute=int(minutes))


def parse_time_window(start: str | None, end: str | None) -> tuple[time, time]:
    """Parse an after-hours window from config fields."""

    return (
        parse_time_of_day(start, field_name="after_hours_start"),
        parse_time_of_day(end, field_name="after_hours_end"),
    )


def get_local_now(timezone_name: str, *, now: datetime | None = None) -> datetime:
    """Return current wall-clock time in ``timezone_name``.

    The optional ``now`` parameter supports deterministic tests.
    """

    resolved_timezone = resolve_timezone(timezone_name)
    reference_time = datetime.now(timezone.utc) if now is None else now

    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    return reference_time.astimezone(resolved_timezone)


__all__ = [
    "TimezoneResolutionError",
    "get_local_now",
    "parse_time_of_day",
    "parse_time_window",
    "resolve_timezone",
]
