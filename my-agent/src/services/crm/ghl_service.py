"""GoHighLevel CRM provider for contact upsert and structured call notes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from hvac_types.call_intake_record import CallIntakeRecord
from services.crm.crm_service import CrmService
from services.crm.mappers import build_contact_note, build_contact_payload
from utils.errors import CrmError
from utils.phone import normalize_phone


class GoHighLevelService(CrmService):
    """Async GoHighLevel v2 client used during call finalization."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        api_token: str,
        location_id: str,
        base_url: str = "https://services.leadconnectorhq.com",
        api_version: str = "2021-07-28",
    ) -> None:
        self._client = client
        self._api_token = api_token
        self._location_id = location_id
        self._base_url = base_url.rstrip("/")
        self._api_version = api_version

    async def upsert_contact(self, record: CallIntakeRecord) -> str:
        """Search, create/update, and annotate a GoHighLevel contact."""

        normalized_phone = normalize_phone(record.phone_number)
        if normalized_phone is None:
            raise CrmError(
                service="gohighlevel",
                operation="normalize_phone",
                detail="valid North American caller phone number required",
            )

        search_response = await self._request(
            "GET",
            "/contacts/",
            operation="search_contact",
            params={
                "locationId": self._location_id,
                "query": normalized_phone,
                "limit": 10,
            },
        )
        contacts = self._extract_contacts(search_response, operation="search_contact")
        matched_contact_id = self._find_exact_phone_match(contacts, normalized_phone)

        if matched_contact_id is None:
            payload = build_contact_payload(record, location_id=self._location_id)
            create_response = await self._request(
                "POST",
                "/contacts/",
                operation="create_contact",
                json_payload=payload,
            )
            contact_id = self._extract_contact_id(
                create_response,
                operation="create_contact",
            )
        else:
            payload = build_contact_payload(record, location_id=self._location_id)
            payload.pop("locationId", None)
            update_response = await self._request(
                "PUT",
                f"/contacts/{matched_contact_id}",
                operation="update_contact",
                json_payload=payload,
            )
            contact_id = self._extract_contact_id(
                update_response,
                operation="update_contact",
                fallback_contact_id=matched_contact_id,
            )

        await self.attach_call_note(contact_id, build_contact_note(record))
        return contact_id

    async def attach_call_note(self, contact_id: str, note_body: str) -> str | None:
        """Attach a structured intake note to an existing CRM contact."""

        response = await self._request(
            "POST",
            f"/contacts/{contact_id}/notes",
            operation="attach_call_note",
            json_payload={"body": note_body},
        )

        payload = self._parse_json_payload(response, operation="attach_call_note")
        note = payload.get("note")
        if isinstance(note, Mapping):
            note_id = note.get("id")
            if note_id:
                return str(note_id)
        return None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        operation: str,
        params: Mapping[str, Any] | None = None,
        json_payload: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"

        try:
            response = await self._client.request(
                method,
                url,
                params=params,
                json=json_payload,
                headers=self._build_headers(),
            )
        except httpx.HTTPError as exc:
            raise CrmError(
                service="gohighlevel",
                operation=operation,
                detail={"error": str(exc), "path": path},
            ) from exc

        if response.status_code >= 400:
            raise CrmError(
                service="gohighlevel",
                operation=operation,
                status_code=response.status_code,
                detail=self._build_failure_detail(response, path=path),
            )

        return response

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Version": self._api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _extract_contacts(
        self,
        response: httpx.Response,
        *,
        operation: str,
    ) -> list[Mapping[str, Any]]:
        payload = self._parse_json_payload(response, operation=operation)
        contacts = payload.get("contacts", [])
        if not isinstance(contacts, list):
            raise CrmError(
                service="gohighlevel",
                operation=operation,
                detail="response missing contacts list",
            )
        return [contact for contact in contacts if isinstance(contact, Mapping)]

    def _extract_contact_id(
        self,
        response: httpx.Response,
        *,
        operation: str,
        fallback_contact_id: str | None = None,
    ) -> str:
        payload = self._parse_json_payload(response, operation=operation)
        contact = payload.get("contact")
        if isinstance(contact, Mapping) and contact.get("id"):
            return str(contact["id"])
        if payload.get("id"):
            return str(payload["id"])
        if fallback_contact_id is not None:
            return fallback_contact_id
        raise CrmError(
            service="gohighlevel",
            operation=operation,
            detail="response missing contact id",
        )

    def _find_exact_phone_match(
        self,
        contacts: list[Mapping[str, Any]],
        normalized_phone: str,
    ) -> str | None:
        for contact in contacts:
            contact_phone = normalize_phone(_coerce_optional_text(contact.get("phone")))
            if contact_phone != normalized_phone:
                continue

            contact_id = contact.get("id")
            if contact_id:
                return str(contact_id)

        return None

    def _parse_json_payload(
        self,
        response: httpx.Response,
        *,
        operation: str,
    ) -> Mapping[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise CrmError(
                service="gohighlevel",
                operation=operation,
                status_code=response.status_code,
                detail="response body was not valid JSON",
            ) from exc

        if not isinstance(payload, Mapping):
            raise CrmError(
                service="gohighlevel",
                operation=operation,
                status_code=response.status_code,
                detail="response body was not a JSON object",
            )
        return payload

    def _build_failure_detail(
        self,
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


__all__ = ["GoHighLevelService"]
