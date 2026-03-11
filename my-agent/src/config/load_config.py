"""Load and validate business configuration for runtime boot."""

from __future__ import annotations

from hvac_types.business_config import BusinessConfig
from utils.time import parse_time_window

from config.hvac_demo_config import HVAC_DEMO_CONFIG

_REQUIRED_FIELDS: tuple[str, ...] = (
    "business_name",
    "timezone",
    "owner_phone",
)
_AFTER_HOURS_FIELDS: tuple[str, ...] = (
    "after_hours_start",
    "after_hours_end",
)


def _is_non_empty_string(value: str | None) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_required_strings(config: BusinessConfig) -> None:
    for field_name in _REQUIRED_FIELDS:
        raw_value = getattr(config, field_name, None)
        if not _is_non_empty_string(raw_value):
            raise ValueError(
                "Invalid BusinessConfig: required field "
                f"'{field_name}' must be a non-empty string."
            )


def _validate_after_hours_window(config: BusinessConfig) -> None:
    for field_name in _AFTER_HOURS_FIELDS:
        raw_value = getattr(config, field_name, None)
        if not _is_non_empty_string(raw_value):
            raise ValueError(
                f"Invalid BusinessConfig: field '{field_name}' must be a non-empty HH:MM string."
            )

    parse_time_window(config.after_hours_start, config.after_hours_end)


def load_config(config: BusinessConfig | None = None) -> BusinessConfig:
    """Return a validated runtime config.

    Falls back to ``HVAC_DEMO_CONFIG`` when ``config`` is not provided.
    Raises ``ValueError`` immediately if required fields are missing, blank,
    or if the after-hours window cannot be parsed.
    """

    resolved_config = HVAC_DEMO_CONFIG if config is None else config
    _validate_required_strings(resolved_config)
    _validate_after_hours_window(resolved_config)

    return resolved_config
