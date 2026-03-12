"""Finalize-once call lifecycle orchestration for CRM + owner alert integrations."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from classification.final_classifier import (
    FinalClassification,
    FinalClassifier,
    FinalClassifierProtocol,
)
from hvac_types.call_intake_record import CallIntakeRecord, CallStatus
from hvac_types.slot_state import SlotStatus
from orchestration.transcript_assembler import TranscriptAssembler
from services.alerts.alert_service import AlertService
from services.crm.crm_service import CrmService
from utils.errors import IntegrationError
from utils.logging import log_lifecycle_event, redact_metadata


class CallLifecycle:
    """Collect transcript events and finalize exactly once when a call ends."""

    _FINALIZE_EVENTS: tuple[str, ...] = ("close", "away", "end")

    def __init__(
        self,
        *,
        controller: Any,
        crm_service: CrmService,
        alert_service: AlertService,
        final_classifier: FinalClassifierProtocol | None = None,
        caller_id: str | None = None,
        logger: Any | None = None,
    ) -> None:
        self._controller = controller
        self._crm_service = crm_service
        self._alert_service = alert_service
        self._final_classifier = final_classifier or FinalClassifier()
        self._caller_id = _clean_text(caller_id)
        self._logger = logger

        self._transcript = TranscriptAssembler()
        self._record: CallIntakeRecord | None = None
        self._attached = False
        self._finalize_lock = asyncio.Lock()

        self._status: dict[str, Any] = {
            "attached": False,
            "finalized": False,
            "finalize_attempts": 0,
            "finalize_trigger": None,
            "call_status": None,
            "transcript_count": 0,
            "caller_id_fallback_used": False,
            "crm_result": {"status": "pending"},
            "sms_result": {"status": "pending"},
        }

    def attach(self, session: Any) -> None:
        """Subscribe to transcript/finalization events on the runtime session."""

        if self._attached:
            return

        session.on("conversation_item_added", self._on_conversation_item_added)
        for event_name in self._FINALIZE_EVENTS:
            session.on(event_name, self._build_finalize_handler(event_name))

        self._attached = True
        self._status["attached"] = True

    async def finalize(self, *, trigger: str = "manual") -> CallIntakeRecord:
        """Finalize the call once and persist integration outcomes."""

        self._status["finalize_attempts"] += 1
        if self._status["finalized"] and self._record is not None:
            log_lifecycle_event(
                self._logger,
                phase="finalize_started",
                status="skipped",
                metadata={
                    "reason": "already_finalized",
                    "trigger": trigger,
                    "attempt": self._status["finalize_attempts"],
                },
            )
            return self._record

        async with self._finalize_lock:
            if self._status["finalized"] and self._record is not None:
                return self._record

            call_status = self._resolve_call_status()
            transcript = self._transcript.render()

            log_lifecycle_event(
                self._logger,
                phase="finalize_started",
                status="ok",
                metadata={
                    "trigger": trigger,
                    "call_status": call_status.value,
                    "transcript_count": self._transcript.line_count,
                },
            )

            final_classification = self._final_classifier.classify(
                controller=self._controller,
                transcript=transcript,
                call_status=call_status,
            )
            record = self._build_record(
                call_status=call_status,
                transcript=transcript,
                final_classification=final_classification,
            )

            crm_result = await self._persist_crm(record)
            sms_result = await self._send_sms(record)

            self._record = record
            self._status.update(
                {
                    "finalized": True,
                    "finalize_trigger": trigger,
                    "call_status": call_status.value,
                    "crm_result": crm_result,
                    "sms_result": sms_result,
                }
            )

            log_lifecycle_event(
                self._logger,
                phase="finalize_completed",
                status="ok",
                metadata={
                    "call_status": call_status.value,
                    "crm_status": crm_result["status"],
                    "sms_status": sms_result["status"],
                },
            )

            return record

    def snapshot(self) -> dict[str, Any]:
        """Return a stable in-memory lifecycle status surface for tests/debugging."""

        snapshot = deepcopy(self._status)
        snapshot["transcript_count"] = self._transcript.line_count

        if self._record is None:
            snapshot["record"] = None
            return snapshot

        snapshot["record"] = _record_snapshot(self._record)
        return snapshot

    def _build_finalize_handler(self, event_name: str):
        async def _handler(*_args: Any, **_kwargs: Any) -> None:
            await self.finalize(trigger=event_name)

        return _handler

    def _on_conversation_item_added(self, payload: Any) -> None:
        accepted = self._transcript.add_event(payload)
        if not accepted:
            return

        self._status["transcript_count"] = self._transcript.line_count
        log_lifecycle_event(
            self._logger,
            phase="transcript_item_added",
            status="ok",
            metadata={"transcript_count": self._transcript.line_count},
        )

    def _resolve_call_status(self) -> CallStatus:
        intake_summary = getattr(
            self._controller, "last_completed_intake_summary", None
        )
        if intake_summary is None:
            return CallStatus.PARTIAL

        missing_required = getattr(intake_summary, "missing_required_slots", ())
        if isinstance(missing_required, tuple) and len(missing_required) == 0:
            return CallStatus.COMPLETE
        return CallStatus.PARTIAL

    def _build_record(
        self,
        *,
        call_status: CallStatus,
        transcript: str,
        final_classification: FinalClassification,
    ) -> CallIntakeRecord:
        intake_summary = getattr(
            self._controller, "last_completed_intake_summary", None
        )

        callback_number, callback_confirmed = _resolved_callback_number(intake_summary)
        used_caller_id_fallback = False
        phone_number = callback_number
        if not callback_confirmed and self._caller_id:
            phone_number = self._caller_id
            used_caller_id_fallback = True

        self._status["caller_id_fallback_used"] = used_caller_id_fallback

        return CallIntakeRecord(
            call_status=call_status,
            customer_name=_slot_text(intake_summary, "customer_name"),
            phone_number=phone_number,
            service_address=_slot_text(intake_summary, "service_address"),
            issue_category=final_classification.issue_category,
            urgency_level=final_classification.urgency_level,
            danger_type=final_classification.danger_type,
            callback_number_confirmed=callback_confirmed,
            caller_id=self._caller_id,
            summary=final_classification.summary,
            notes=_build_notes(
                controller=self._controller,
                fallback_used=used_caller_id_fallback,
            ),
            transcript=transcript or None,
            ai_summary=final_classification.ai_summary,
            notify_owner=final_classification.notify_owner,
        )

    async def _persist_crm(self, record: CallIntakeRecord) -> dict[str, Any]:
        try:
            contact_id = await self._crm_service.upsert_contact(record)
        except Exception as exc:  # noqa: BLE001 - lifecycle snapshots intentionally capture all failure paths
            result = {
                "status": "error",
                "error": _error_payload(exc),
            }
            log_lifecycle_event(
                self._logger,
                phase="crm_result",
                status="error",
                metadata=result,
            )
            return result

        result = {"status": "ok", "contact_id": contact_id}
        log_lifecycle_event(
            self._logger,
            phase="crm_result",
            status="ok",
            metadata={"status": "ok"},
        )
        return result

    async def _send_sms(self, record: CallIntakeRecord) -> dict[str, Any]:
        if record.notify_owner is not True:
            result = {"status": "skipped", "reason": "notify_owner_false"}
            log_lifecycle_event(
                self._logger,
                phase="sms_result",
                status="skipped",
                metadata=result,
            )
            return result

        try:
            sms_sent = await self._alert_service.send_owner_sms(record)
        except Exception as exc:  # noqa: BLE001 - lifecycle snapshots intentionally capture all failure paths
            result = {
                "status": "error",
                "error": _error_payload(exc),
            }
            log_lifecycle_event(
                self._logger,
                phase="sms_result",
                status="error",
                metadata=result,
            )
            return result

        if sms_sent:
            record.sms_sent = True

        result = {"status": "ok", "sent": bool(sms_sent)}
        log_lifecycle_event(
            self._logger,
            phase="sms_result",
            status="ok",
            metadata={"status": "ok", "sent": bool(sms_sent)},
        )
        return result


def _slot_text(intake_summary: Any | None, slot_name: str) -> str | None:
    if intake_summary is None:
        return None

    slots = getattr(intake_summary, "slots", None)
    if not isinstance(slots, dict):
        return None

    slot_state = slots.get(slot_name)
    if slot_state is None:
        return None

    value = getattr(slot_state, "value", None)
    return _clean_text(value)


def _resolved_callback_number(intake_summary: Any | None) -> tuple[str | None, bool]:
    if intake_summary is None:
        return None, False

    slots = getattr(intake_summary, "slots", None)
    if not isinstance(slots, dict):
        return None, False

    slot_state = slots.get("phone_number")
    if slot_state is None:
        return None, False

    value = _clean_text(getattr(slot_state, "value", None))
    is_confirmed = (
        getattr(slot_state, "status", None) == SlotStatus.CONFIRMED
        and value is not None
    )

    return value, is_confirmed


def _build_notes(*, controller: Any, fallback_used: bool) -> str | None:
    mode = _clean_text(getattr(controller, "current_mode", None))
    handoff_state = getattr(controller, "handoff_state", None)

    parts: list[str] = []
    if mode:
        parts.append(f"mode={mode}")
    if handoff_state is not None:
        reason = _clean_text(getattr(handoff_state, "reason", None))
        if reason:
            parts.append(f"handoff_reason={reason}")
    if fallback_used:
        parts.append("caller_id_fallback_used=true")

    if not parts:
        return None

    return "; ".join(parts)


def _record_snapshot(record: CallIntakeRecord) -> dict[str, Any]:
    raw = asdict(record) if is_dataclass(record) else record.__dict__.copy()

    snapshot: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, Enum):
            snapshot[key] = value.value
        else:
            snapshot[key] = value

    if "transcript" in snapshot and snapshot["transcript"]:
        snapshot["transcript"] = "[stored]"

    return snapshot


def _error_payload(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, IntegrationError):
        return dict(exc.to_dict())

    payload = {
        "type": exc.__class__.__name__,
        "message": str(exc),
    }
    return redact_metadata(payload)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None
    return text


__all__ = ["CallLifecycle"]
