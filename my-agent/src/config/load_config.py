"""Load and validate business configuration for runtime boot."""

from __future__ import annotations

from hvac_types.business_config import BusinessConfig

from config.hvac_demo_config import HVAC_DEMO_CONFIG

_REQUIRED_FIELDS: tuple[str, ...] = ("business_name", "timezone", "owner_phone")


def _is_non_empty_string(value: str | None) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_config(config: BusinessConfig | None = None) -> BusinessConfig:
    """Return a validated runtime config.

    Falls back to ``HVAC_DEMO_CONFIG`` when ``config`` is not provided.
    Raises ``ValueError`` immediately if required fields are missing or blank.
    """

    resolved_config = HVAC_DEMO_CONFIG if config is None else config

    for field_name in _REQUIRED_FIELDS:
        raw_value = getattr(resolved_config, field_name, None)
        if not _is_non_empty_string(raw_value):
            raise ValueError(
                f"Invalid BusinessConfig: required field '{field_name}' must be a non-empty string."
            )

    return resolved_config
