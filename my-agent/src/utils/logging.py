"""Structured logging helpers for lifecycle orchestration."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from typing import Any

_SENSITIVE_KEY_PATTERN = re.compile(
    r"(token|secret|password|authorization|api[_-]?key|transcript)",
    re.IGNORECASE,
)
_BEARER_PATTERN = re.compile(r"Bearer\s+[^\s,;]+", re.IGNORECASE)
_BASIC_PATTERN = re.compile(r"Basic\s+[^\s,;]+", re.IGNORECASE)


def get_logger(name: str) -> logging.Logger:
    """Return a standard Python logger for runtime lifecycle events."""

    return logging.getLogger(name)


def log_lifecycle_event(
    logger: logging.Logger | None,
    *,
    phase: str,
    status: str,
    metadata: Mapping[str, Any] | None = None,
) -> None:
    """Emit one structured lifecycle log line with redacted metadata."""

    if logger is None:
        return

    payload = {
        "phase": phase,
        "status": status,
        "metadata": redact_metadata(metadata or {}),
    }

    log_method = logger.info if status not in {"error", "failed"} else logger.warning
    log_method("lifecycle_event %s", json.dumps(payload, sort_keys=True))


def redact_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Return metadata safe for logs (no secrets/raw transcript payloads)."""

    redacted: dict[str, Any] = {}
    for key, value in metadata.items():
        key_text = str(key)
        if _SENSITIVE_KEY_PATTERN.search(key_text):
            redacted[key_text] = "[redacted]"
            continue
        redacted[key_text] = _redact_value(value)

    return redacted


def _redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return redact_metadata(value)
    if isinstance(value, (list, tuple, set)):
        return [_redact_value(item) for item in value]

    text = str(value)
    text = _BEARER_PATTERN.sub("Bearer [redacted]", text)
    text = _BASIC_PATTERN.sub("Basic [redacted]", text)
    if text != str(value):
        return text

    return value


__all__ = ["get_logger", "log_lifecycle_event", "redact_metadata"]
