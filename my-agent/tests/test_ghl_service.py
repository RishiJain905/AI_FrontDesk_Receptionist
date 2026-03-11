from __future__ import annotations

import json

import httpx
import pytest

from hvac_types.call_intake_record import CallIntakeRecord, CallStatus
from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel
from services.crm.ghl_service import GoHighLevelService
from services.crm.mappers import build_contact_note, build_contact_payload
from utils.errors import CrmError


@pytest.fixture
def finalized_record() -> CallIntakeRecord:
    return CallIntakeRecord(
        call_status=CallStatus.COMPLETE,
        customer_name="Jordan Example",
        phone_number="416-555-0199",
        service_address="14 King Street West, Toronto, ON",
        issue_category=IssueCategory.NO_HEAT,
        urgency_level=UrgencyLevel.EMERGENCY,
        danger_type=DangerType.GAS_LEAK,
        callback_requested=True,
        callback_time="Tomorrow after 8 AM",
        customer_type="existing",
        summary="Furnace shut off overnight and the house is getting cold.",
        transcript="Caller says the furnace stopped overnight and there is a faint gas smell.",
        ai_summary="Existing customer with an emergency no-heat call who wants a callback after 8 AM.",
        notify_owner=True,
        sms_sent=False,
    )


def test_build_contact_payload_maps_record_into_deterministic_contact_fields(
    finalized_record: CallIntakeRecord,
) -> None:
    assert build_contact_payload(finalized_record, location_id="loc-123") == {
        "locationId": "loc-123",
        "firstName": "Jordan Example",
        "phone": "+14165550199",
        "address1": "14 King Street West, Toronto, ON",
    }


def test_build_contact_note_includes_structured_classification_and_summary_sections(
    finalized_record: CallIntakeRecord,
) -> None:
    assert build_contact_note(finalized_record) == (
        "Call Status: complete\n"
        "Issue Category: no_heat\n"
        "Urgency Level: emergency\n"
        "Danger Type: gas_leak\n"
        "Customer Type: existing\n"
        "Callback Requested: yes\n"
        "Callback Time: Tomorrow after 8 AM\n"
        "Summary: Furnace shut off overnight and the house is getting cold.\n"
        "Transcript:\n"
        "Caller says the furnace stopped overnight and there is a faint gas smell.\n"
        "AI Summary:\n"
        "Existing customer with an emergency no-heat call who wants a callback after 8 AM."
    )


@pytest.mark.asyncio
async def test_upsert_contact_creates_new_contact_and_attaches_note_when_no_exact_match_exists(
    finalized_record: CallIntakeRecord,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if request.method == "GET":
            assert request.url == httpx.URL(
                "https://services.leadconnectorhq.com/contacts/?locationId=loc-123&query=%2B14165550199&limit=10"
            )
            assert request.headers["Authorization"] == "Bearer ghl-secret-token"
            assert request.headers["Version"] == "2021-07-28"
            return httpx.Response(200, json={"contacts": []})

        if request.method == "POST" and request.url.path == "/contacts/":
            assert request.headers["Content-Type"] == "application/json"
            assert json.loads(request.content.decode()) == build_contact_payload(
                finalized_record,
                location_id="loc-123",
            )
            return httpx.Response(201, json={"contact": {"id": "contact-123"}})

        if request.method == "POST" and request.url.path == "/contacts/contact-123/notes":
            assert json.loads(request.content.decode()) == {
                "body": build_contact_note(finalized_record)
            }
            return httpx.Response(201, json={"note": {"id": "note-001"}})

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GoHighLevelService(
            client=client,
            api_token="ghl-secret-token",
            location_id="loc-123",
        )

        contact_id = await service.upsert_contact(finalized_record)

    assert contact_id == "contact-123"
    assert [request.method for request in requests] == ["GET", "POST", "POST"]


@pytest.mark.asyncio
async def test_upsert_contact_creates_new_contact_when_search_returns_only_non_matching_phones(
    finalized_record: CallIntakeRecord,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "contacts": [
                        {"id": "contact-elsewhere", "phone": "+1 416 555 0000"},
                    ]
                },
            )

        if request.method == "POST" and request.url.path == "/contacts/":
            return httpx.Response(201, json={"contact": {"id": "contact-123"}})

        if request.method == "POST" and request.url.path == "/contacts/contact-123/notes":
            return httpx.Response(201, json={"note": {"id": "note-001"}})

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GoHighLevelService(
            client=client,
            api_token="ghl-secret-token",
            location_id="loc-123",
        )

        contact_id = await service.upsert_contact(finalized_record)

    assert contact_id == "contact-123"
    assert [request.method for request in requests] == ["GET", "POST", "POST"]


@pytest.mark.asyncio
async def test_upsert_contact_updates_exact_phone_match_then_attaches_note(
    finalized_record: CallIntakeRecord,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "contacts": [
                        {"id": "contact-999", "phone": "1 (416) 555-0199"},
                    ]
                },
            )

        if request.method == "PUT" and request.url.path == "/contacts/contact-999":
            assert json.loads(request.content.decode()) == {
                "firstName": "Jordan Example",
                "phone": "+14165550199",
                "address1": "14 King Street West, Toronto, ON",
            }
            return httpx.Response(200, json={"contact": {"id": "contact-999"}})

        if request.method == "POST" and request.url.path == "/contacts/contact-999/notes":
            assert json.loads(request.content.decode()) == {
                "body": build_contact_note(finalized_record)
            }
            return httpx.Response(201, json={"note": {"id": "note-002"}})

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GoHighLevelService(
            client=client,
            api_token="ghl-secret-token",
            location_id="loc-123",
        )

        contact_id = await service.upsert_contact(finalized_record)

    assert contact_id == "contact-999"
    assert [request.method for request in requests] == ["GET", "PUT", "POST"]


@pytest.mark.asyncio
async def test_upsert_contact_raises_typed_crm_error_with_stable_metadata_on_http_failure(
    finalized_record: CallIntakeRecord,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(502, json={"message": "upstream unavailable"})
    )

    async with httpx.AsyncClient(transport=transport) as client:
        service = GoHighLevelService(
            client=client,
            api_token="ghl-secret-token",
            location_id="loc-123",
        )

        with pytest.raises(CrmError) as exc_info:
            await service.upsert_contact(finalized_record)

    error = exc_info.value
    assert error.service == "gohighlevel"
    assert error.operation == "search_contact"
    assert error.status_code == 502
    assert "ghl-secret-token" not in str(error)
