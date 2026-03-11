"""Typed integration error surfaces with stable metadata and redacted detail."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

_REDACTED = "[redacted]"
_MAX_DETAIL_LENGTH = 240
_SENSITIVE_KEY_PATTERN = re.compile(
    r"(token|secret|password|authorization|api[_-]?key|transcript)",
    re.IGNORECASE,
)
_BEARER_PATTERN = re.compile(r"Bearer\s+[^\s,;]+", re.IGNORECASE)
_BASIC_PATTERN = re.compile(r"Basic\s+[^\s,;]+", re.IGNORECASE)
_LONG_SECRET_PATTERN = re.compile(r"\b[A-Za-z0-9_-]{24,}\b")


class IntegrationError(Exception):
    """Base error for external integration failures.

    Attributes remain stable for tests, retries, and future observability:
    ``service`` identifies the downstream system, ``operation`` identifies the
    failed step, and ``status_code`` keeps the HTTP status when available.
    """

    def __init__(
        self,
        *,
        service: str,
        operation: str,
        status_code: int | None = None,
        detail: Any | None = None,
    ) -> None:
        self.service = service
        self.operation = operation
        self.status_code = status_code
        self.detail = self._redact_detail(detail)
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        status_segment = ""
        if self.status_code is not None:
            status_segment = f" status_code={self.status_code}"

        message = f"{self.service} {self.operation} failed{status_segment}"
        if self.detail:
            message = f"{message}: {self.detail}"
        return message

    @classmethod
    def _redact_detail(cls, detail: Any | None) -> str | None:
        if detail is None:
            return None

        serialized = cls._serialize_detail(detail)
        if serialized is None:
            return None

        redacted = _BEARER_PATTERN.sub(f"Bearer {_REDACTED}", serialized)
        redacted = _BASIC_PATTERN.sub(f"Basic {_REDACTED}", redacted)
        redacted = _LONG_SECRET_PATTERN.sub(_REDACTED, redacted)

        if len(redacted) > _MAX_DETAIL_LENGTH:
            return f"{redacted[:_MAX_DETAIL_LENGTH].rstrip()}…"
        return redacted

    @classmethod
    def _serialize_detail(cls, detail: Any) -> str | None:
        if isinstance(detail, Mapping):
            return json.dumps(cls._sanitize_mapping(detail), sort_keys=True)
        if isinstance(detail, (list, tuple, set)):
            return json.dumps([cls._sanitize_value(value) for value in detail])

        text = str(detail).strip()
        if not text:
            return None
        return text

    @classmethod
    def _sanitize_mapping(cls, detail: Mapping[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}
        for key, value in detail.items():
            if _SENSITIVE_KEY_PATTERN.search(str(key)):
                sanitized[str(key)] = _REDACTED
            else:
                sanitized[str(key)] = cls._sanitize_value(value)
        return sanitized

    @classmethod
    def _sanitize_value(cls, value: Any) -> Any:
        if isinstance(value, Mapping):
            return cls._sanitize_mapping(value)
        if isinstance(value, (list, tuple, set)):
            return [cls._sanitize_value(item) for item in value]

        text = str(value)
        if _BEARER_PATTERN.search(text) or _BASIC_PATTERN.search(text):
            return _REDACTED
        if len(text) > _MAX_DETAIL_LENGTH:
            return f"{text[:_MAX_DETAIL_LENGTH].rstrip()}…"
        return value

    def to_dict(self) -> dict[str, Any]:
        """Return a stable diagnostic shape for logs/tests without secrets."""

        return {
            "service": self.service,
            "operation": self.operation,
            "status_code": self.status_code,
            "detail": self.detail,
        }


class CrmError(IntegrationError):
    """Integration error raised by CRM providers."""

    def __init__(
        self,
        *,
        operation: str,
        service: str = "crm",
        status_code: int | None = None,
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            service=service,
            operation=operation,
            status_code=status_code,
            detail=detail,
        )


class SmsError(IntegrationError):
    """Integration error raised by outbound SMS providers."""

    def __init__(
        self,
        *,
        operation: str,
        service: str = "sms",
        status_code: int | None = None,
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            service=service,
            operation=operation,
            status_code=status_code,
            detail=detail,
        )
