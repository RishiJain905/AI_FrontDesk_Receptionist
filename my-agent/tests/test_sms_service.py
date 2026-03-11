from __future__ import annotations

from urllib.parse import parse_qs

import httpx
import pytest

from hvac_types.business_config import BusinessConfig
from hvac_types.call_intake_record import CallIntakeRecord, CallStatus
from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel
from services.alerts.sms_service import TwilioSmsService, build_owner_alert_text
from utils.errors import SmsError


@pytest.fixture
def business_config() -> BusinessConfig:
    return BusinessConfig(owner_phone="416-555-0100")


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
        summary="Furnace shut off overnight and the house is getting cold.",
        notify_owner=True,
        sms_sent=False,
    )


def test_build_owner_alert_text_formats_concise_owner_message(
    finalized_record: CallIntakeRecord,
) -> None:
    assert build_owner_alert_text(finalized_record) == (
        "HVAC alert: Jordan Example (+14165550199) reported Furnace shut off overnight "
        "and the house is getting cold. Urgency: emergency."
    )


@pytest.mark.asyncio
async def test_send_owner_alert_posts_twilio_form_request_with_basic_auth(
    finalized_record: CallIntakeRecord,
    business_config: BusinessConfig,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "POST"
        assert request.url == httpx.URL(
            "https://api.twilio.com/2010-04-01/Accounts/AC123/Messages.json"
        )
        assert request.headers["Authorization"].startswith("Basic ")
        assert request.headers["Content-Type"].startswith(
            "application/x-www-form-urlencoded"
        )

        form = parse_qs(request.content.decode())
        assert form == {
            "To": ["+14165550100"],
            "From": ["+14165550000"],
            "Body": [build_owner_alert_text(finalized_record)],
        }
        return httpx.Response(201, json={"sid": "SM123"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = TwilioSmsService(
            client=client,
            business_config=business_config,
            account_sid="AC123",
            auth_token="twilio-secret-token",
            from_number="+14165550000",
        )

        sent = await service.send_owner_alert(finalized_record)

    assert sent is True
    assert len(requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("notify_owner", "sms_sent"),
    [
        (False, False),
        (True, True),
    ],
)
async def test_send_owner_alert_skips_outbound_request_when_notification_is_disabled_or_already_sent(
    business_config: BusinessConfig,
    notify_owner: bool,
    sms_sent: bool,
) -> None:
    requests: list[httpx.Request] = []

    record = CallIntakeRecord(
        call_status=CallStatus.COMPLETE,
        customer_name="Jordan Example",
        phone_number="416-555-0199",
        summary="Furnace shut off overnight and the house is getting cold.",
        urgency_level=UrgencyLevel.EMERGENCY,
        notify_owner=notify_owner,
        sms_sent=sms_sent,
    )

    transport = httpx.MockTransport(
        lambda request: requests.append(request) or httpx.Response(201, json={"sid": "SM123"})
    )

    async with httpx.AsyncClient(transport=transport) as client:
        service = TwilioSmsService(
            client=client,
            business_config=business_config,
            account_sid="AC123",
            auth_token="twilio-secret-token",
            from_number="+14165550000",
        )

        sent = await service.send_owner_alert(record)

    assert sent is False
    assert requests == []


@pytest.mark.asyncio
async def test_send_owner_alert_raises_typed_sms_error_with_stable_metadata_on_http_failure(
    finalized_record: CallIntakeRecord,
    business_config: BusinessConfig,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(401, json={"message": "auth failure"})
    )

    async with httpx.AsyncClient(transport=transport) as client:
        service = TwilioSmsService(
            client=client,
            business_config=business_config,
            account_sid="AC123",
            auth_token="twilio-secret-token",
            from_number="+14165550000",
        )

        with pytest.raises(SmsError) as exc_info:
            await service.send_owner_alert(finalized_record)

    error = exc_info.value
    assert error.service == "twilio"
    assert error.operation == "send_sms"
    assert error.status_code == 401
    assert "twilio-secret-token" not in str(error)
