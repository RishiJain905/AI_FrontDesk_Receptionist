"""Twilio SMS provider for concise owner alerts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from hvac_types.business_config import BusinessConfig
from hvac_types.call_intake_record import CallIntakeRecord
from services.alerts.alert_service import AlertService
from utils.errors import SmsError
from utils.phone import normalize_phone


class TwilioSmsService(AlertService):
    """Async Twilio client used to send owner alerts during finalization."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        business_config: BusinessConfig,
        account_sid: str,
        auth_token: str,
        from_number: str,
        base_url: str = "https://api.twilio.com",
    ) -> None:
        self._client = client
        self._business_config = business_config
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._from_number = from_number
        self._base_url = base_url.rstrip("/")

    async def send_owner_sms(self, record: CallIntakeRecord) -> bool:
        """Send the owner alert when enabled and not already sent."""

        return await self.send_owner_alert(record)

    async def send_owner_alert(self, record: CallIntakeRecord) -> bool:
        """Compatibility wrapper used by the S04 tests and downstream callers."""

        if record.notify_owner is not True or record.sms_sent is True:
            return False

        destination_number = normalize_phone(self._business_config.owner_phone)
        if destination_number is None:
            raise SmsError(
                service="twilio",
                operation="normalize_phone",
                detail="valid North American owner phone number required",
            )

        sender_number = normalize_phone(self._from_number)
        if sender_number is None:
            raise SmsError(
                service="twilio",
                operation="normalize_phone",
                detail="valid North American Twilio from number required",
            )

        try:
            response = await self._client.post(
                self._messages_url,
                data={
                    "To": destination_number,
                    "From": sender_number,
                    "Body": build_owner_alert_text(record),
                },
                auth=(self._account_sid, self._auth_token),
            )
        except httpx.HTTPError as exc:
            raise SmsError(
                service="twilio",
                operation="send_sms",
                detail={"error": str(exc), "path": self._messages_path},
            ) from exc

        if response.status_code >= 400:
            raise SmsError(
                service="twilio",
                operation="send_sms",
                status_code=response.status_code,
                detail=_build_failure_detail(response, path=self._messages_path),
            )

        return True

    @property
    def _messages_path(self) -> str:
        return f"/2010-04-01/Accounts/{self._account_sid}/Messages.json"

    @property
    def _messages_url(self) -> str:
        return f"{self._base_url}{self._messages_path}"


def build_owner_alert_text(record: CallIntakeRecord) -> str:
    """Render a concise, action-oriented owner alert message."""

    caller_name = _coerce_optional_text(record.customer_name) or "Unknown caller"
    callback_number = normalize_phone(record.phone_number) or (
        _coerce_optional_text(record.phone_number) or "unknown number"
    )

    summary = _coerce_optional_text(record.summary)
    if summary is None:
        summary = _build_summary_fallback(record)

    alert = f"HVAC alert: {caller_name} ({callback_number}) reported {summary}"

    urgency = _coerce_optional_text(record.urgency_level)
    if urgency:
        alert = f"{alert} Urgency: {urgency}."
    else:
        alert = f"{alert}."

    return alert


def _build_summary_fallback(record: CallIntakeRecord) -> str:
    parts: list[str] = []

    issue = _coerce_optional_text(record.issue_category)
    if issue:
        parts.append(issue.replace("_", " "))

    danger = _coerce_optional_text(record.danger_type)
    if danger:
        parts.append(f"danger: {danger.replace('_', ' ')}")

    if not parts:
        return "an HVAC issue"

    return ", ".join(parts)


def _build_failure_detail(
    response: httpx.Response,
    *,
    path: str,
) -> Mapping[str, str]:
    detail: dict[str, str] = {"path": path}

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, Mapping):
        for key in ("message", "error", "detail"):
            value = payload.get(key)
            text = _coerce_optional_text(value)
            if text:
                detail["message"] = text
                break
    else:
        text = _coerce_optional_text(response.text)
        if text:
            detail["message"] = text

    return detail


def _coerce_optional_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None
    return text


__all__ = ["TwilioSmsService", "build_owner_alert_text"]
