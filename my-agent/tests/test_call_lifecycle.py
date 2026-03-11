from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

import classification.final_classifier as final_classifier_module
from hvac_types.call_intake_record import CallIntakeRecord, CallStatus
from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel
from hvac_types.slot_state import SlotState, SlotStatus
from orchestration.call_lifecycle import CallLifecycle
from utils.errors import CrmError, SmsError
import utils.logging as logging_utils


@dataclass
class FakeConversationItem:
    role: str
    text_content: str
    type: str = "message"
    interrupted: bool = False


@dataclass
class FakeIntakeSummary:
    slots: dict[str, SlotState]
    missing_required_slots: tuple[str, ...] = ()


class FakeSession:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Any]] = {}

    def on(self, event_name: str, handler: Any) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    async def emit(self, event_name: str, payload: Any | None = None) -> None:
        for handler in self._handlers.get(event_name, []):
            result = handler(payload) if payload is not None else handler()
            if hasattr(result, "__await__"):
                await result


class FakeCrmService:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.records: list[CallIntakeRecord] = []
        self.upsert_calls = 0

    async def upsert_contact(self, record: CallIntakeRecord) -> str:
        self.upsert_calls += 1
        self.records.append(record)
        if self.error is not None:
            raise self.error
        return "contact-123"

    async def attach_call_note(self, contact_id: str, note_body: str) -> str | None:
        return f"note-for-{contact_id}:{len(note_body)}"


class FakeAlertService:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls = 0

    async def send_owner_sms(self, record: CallIntakeRecord) -> bool:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return True


class FakeFinalClassifier:
    def classify(
        self,
        *,
        controller: Any,
        transcript: str,
        call_status: CallStatus,
    ) -> Any:
        return SimpleNamespace(
            issue_category=IssueCategory.NO_HEAT,
            urgency_level=UrgencyLevel.URGENT,
            danger_type=DangerType.NONE,
            summary="Furnace stopped overnight.",
            ai_summary=f"{call_status.value}:{transcript[:40]}",
            notify_owner=True,
        )


class FakeController:
    def __init__(
        self,
        *,
        completed: bool,
        callback_number: str | None,
        callback_confirmed: bool,
    ) -> None:
        phone_state = SlotStatus.CONFIRMED if callback_confirmed else SlotStatus.FILLED
        slots = {
            "customer_name": SlotState(status=SlotStatus.CONFIRMED, value="Jordan Example"),
            "phone_number": SlotState(status=phone_state, value=callback_number),
            "service_address": SlotState(
                status=SlotStatus.CONFIRMED,
                value="14 King Street West, Toronto",
            ),
        }
        self.last_completed_intake_summary = (
            FakeIntakeSummary(slots=slots, missing_required_slots=()) if completed else None
        )
        self.latest_classification = SimpleNamespace(
            issue_category=IssueCategory.NO_HEAT,
            urgency_level=UrgencyLevel.URGENT,
            danger_type=DangerType.NONE,
        )
        self.handoff_state = None


def _new_lifecycle(
    *,
    controller: FakeController,
    crm_error: Exception | None = None,
    sms_error: Exception | None = None,
    caller_id: str = "+1-416-555-0144",
) -> tuple[CallLifecycle, FakeSession, FakeCrmService, FakeAlertService]:
    session = FakeSession()
    crm = FakeCrmService(error=crm_error)
    alerts = FakeAlertService(error=sms_error)
    logger_factory = getattr(logging_utils, "get_logger", lambda _name: None)
    lifecycle = CallLifecycle(
        controller=controller,
        crm_service=crm,
        alert_service=alerts,
        final_classifier=FakeFinalClassifier(),
        caller_id=caller_id,
        logger=logger_factory("tests.call_lifecycle"),
    )
    lifecycle.attach(session)
    return lifecycle, session, crm, alerts


@pytest.mark.asyncio
async def test_lifecycle_assembles_ordered_transcript_and_finalizes_complete_calls() -> None:
    _, session, crm, _ = _new_lifecycle(
        controller=FakeController(
            completed=True,
            callback_number="416-555-0199",
            callback_confirmed=True,
        )
    )

    await session.emit("conversation_item_added", FakeConversationItem("user", "Hi there"))
    await session.emit(
        "conversation_item_added",
        FakeConversationItem("assistant", "North Star HVAC after-hours dispatch."),
    )
    await session.emit(
        "conversation_item_added",
        FakeConversationItem("user", "My furnace has no heat."),
    )
    await session.emit("close")

    assert crm.upsert_calls == 1
    record = crm.records[0]
    assert record.call_status == CallStatus.COMPLETE
    assert record.transcript is not None
    assert record.transcript.index("Hi there") < record.transcript.index("My furnace has no heat")


@pytest.mark.asyncio
async def test_lifecycle_uses_caller_id_fallback_when_callback_not_confirmed() -> None:
    lifecycle, session, crm, _ = _new_lifecycle(
        controller=FakeController(
            completed=False,
            callback_number=None,
            callback_confirmed=False,
        ),
        caller_id="+1-416-555-0888",
    )

    await session.emit(
        "conversation_item_added",
        FakeConversationItem("user", "My place is freezing and my callback number is maybe 416..."),
    )
    await session.emit("close")

    record = crm.records[0]
    assert record.call_status == CallStatus.PARTIAL
    assert record.phone_number == "+1-416-555-0888"
    assert record.caller_id == "+1-416-555-0888"
    assert record.callback_number_confirmed is False

    snapshot = lifecycle.snapshot()
    assert snapshot["finalized"] is True
    assert snapshot["call_status"] == "partial"


@pytest.mark.asyncio
async def test_lifecycle_finalize_is_idempotent_even_with_duplicate_close_events() -> None:
    _, session, crm, alerts = _new_lifecycle(
        controller=FakeController(
            completed=True,
            callback_number="416-555-0199",
            callback_confirmed=True,
        )
    )

    await session.emit("close")
    await session.emit("close")

    assert crm.upsert_calls == 1
    assert alerts.calls == 1


@pytest.mark.asyncio
async def test_lifecycle_records_structured_provider_failures_without_blocking_other_provider() -> None:
    crm_error = CrmError(
        service="gohighlevel",
        operation="upsert_contact",
        status_code=502,
        detail={"token": "ghl-secret-token", "message": "upstream unavailable"},
    )
    sms_error = SmsError(
        service="twilio",
        operation="send_sms",
        status_code=503,
        detail={"authorization": "Bearer very-secret", "message": "gateway timeout"},
    )

    lifecycle, session, _, alerts = _new_lifecycle(
        controller=FakeController(
            completed=True,
            callback_number="416-555-0199",
            callback_confirmed=True,
        ),
        crm_error=crm_error,
        sms_error=sms_error,
    )

    await session.emit("conversation_item_added", FakeConversationItem("user", "No heat."))
    await session.emit("close")

    assert alerts.calls == 1
    snapshot = lifecycle.snapshot()
    assert snapshot["crm_result"]["status"] == "error"
    assert snapshot["crm_result"]["error"]["service"] == "gohighlevel"
    assert snapshot["crm_result"]["error"]["operation"] == "upsert_contact"
    assert snapshot["sms_result"]["status"] == "error"
    assert snapshot["sms_result"]["error"]["service"] == "twilio"
    assert "very-secret" not in str(snapshot)


def test_lifecycle_boundary_modules_load_from_planned_s05_surfaces() -> None:
    assert final_classifier_module.__name__ == "classification.final_classifier"
    assert logging_utils.__name__ == "utils.logging"
