import json
import logging
import os
from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

import httpx
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from config.load_config import load_config
from conversation.conversation_controller import HVACConversationController
from hvac_types.business_config import BusinessConfig
from orchestration.after_hours_gate import is_after_hours
from orchestration.call_lifecycle import CallLifecycle
from services.alerts.sms_service import TwilioSmsService
from services.crm.ghl_service import GoHighLevelService
from utils.logging import get_logger, log_lifecycle_event
from utils.phone import normalize_phone

logger = logging.getLogger("agent")

load_dotenv(".env.local")
load_dotenv(".env")

server = AgentServer()


class _NoopCrmService:
    async def upsert_contact(self, _record: Any) -> str:
        return "noop-contact"

    async def attach_call_note(self, _contact_id: str, _note_body: str) -> str | None:
        return None


class _NoopAlertService:
    async def send_owner_sms(self, _record: Any) -> bool:
        return False


_CALLER_ID_KEYS: tuple[str, ...] = (
    "caller_id",
    "callerId",
    "phone_number",
    "phoneNumber",
    "phone",
    "ani",
    "from",
    "from_number",
)



def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None
    return text


def _extract_phone_from_mapping(payload: Mapping[str, Any]) -> str | None:
    for key in _CALLER_ID_KEYS:
        if key not in payload:
            continue

        raw_value = _clean_text(payload[key])
        if raw_value is None:
            continue

        normalized = normalize_phone(raw_value)
        if normalized is not None:
            return normalized

    return None


def _extract_caller_id_from_candidate(candidate: Any) -> str | None:
    if isinstance(candidate, Mapping):
        return _extract_phone_from_mapping(candidate)

    if isinstance(candidate, (list, tuple)):
        for item in candidate:
            resolved = _extract_caller_id_from_candidate(item)
            if resolved is not None:
                return resolved
        return None

    candidate_text = _clean_text(candidate)
    if candidate_text is None:
        return None

    try:
        payload = json.loads(candidate_text)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, Mapping):
        return _extract_phone_from_mapping(payload)

    return normalize_phone(candidate_text)


def _iter_room_participants(room: Any) -> list[Any]:
    remote_participants = getattr(room, "remote_participants", None)
    if isinstance(remote_participants, Mapping):
        return list(remote_participants.values())
    if isinstance(remote_participants, list):
        return remote_participants
    return []


def _resolve_caller_id(ctx: JobContext) -> str | None:
    room = getattr(ctx, "room", None)

    metadata_candidates: list[Any] = [
        getattr(ctx, "metadata", None),
        getattr(getattr(ctx, "job", None), "metadata", None),
        getattr(room, "metadata", None),
    ]

    for participant in _iter_room_participants(room):
        metadata_candidates.extend(
            [
                getattr(participant, "attributes", None),
                getattr(participant, "metadata", None),
                getattr(participant, "identity", None),
                getattr(participant, "phone_number", None),
                getattr(participant, "sip_phone_number", None),
            ]
        )

    for candidate in metadata_candidates:
        caller_id = _extract_caller_id_from_candidate(candidate)
        if caller_id is not None:
            return caller_id

    return None


def _build_crm_service(*, client: httpx.AsyncClient) -> Any:
    api_token = _clean_text(os.getenv("GHL_API_TOKEN"))
    location_id = _clean_text(os.getenv("GHL_LOCATION_ID"))
    if api_token and location_id:
        return GoHighLevelService(
            client=client,
            api_token=api_token,
            location_id=location_id,
        )

    logger.info(
        "CRM provider not configured; using no-op CRM service (set GHL_API_TOKEN and GHL_LOCATION_ID)."
    )
    return _NoopCrmService()


def _build_alert_service(*, client: httpx.AsyncClient, business_config: BusinessConfig) -> Any:
    account_sid = _clean_text(os.getenv("TWILIO_ACCOUNT_SID"))
    auth_token = _clean_text(os.getenv("TWILIO_AUTH_TOKEN"))
    from_number = _clean_text(os.getenv("TWILIO_FROM_NUMBER"))
    if account_sid and auth_token and from_number:
        return TwilioSmsService(
            client=client,
            business_config=business_config,
            account_sid=account_sid,
            auth_token=auth_token,
            from_number=from_number,
        )

    logger.info(
        "SMS provider not configured; using no-op alert service (set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER)."
    )
    return _NoopAlertService()


def build_runtime_agent(
    config: BusinessConfig | HVACConversationController | None = None,
) -> HVACConversationController:
    """Create the slice-composed conversation controller for the LiveKit session."""

    if isinstance(config, HVACConversationController):
        return config

    runtime_config = load_config(config)
    return HVACConversationController(config=runtime_config)


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    lifecycle_logger = get_logger("agent.lifecycle")

    runtime_config = load_config()
    gate_decision = is_after_hours(runtime_config)
    gate_mode = "after_hours" if gate_decision.is_after_hours else "outside_hours_passthrough"
    log_lifecycle_event(
        lifecycle_logger,
        phase="gate_checked",
        status="ok",
        metadata={
            **asdict(gate_decision),
            "mode": gate_mode,
        },
    )

    if not gate_decision.is_after_hours:
        logger.info(
            "Call started outside configured after-hours window; continuing with graceful pass-through runtime flow."
        )

    integration_client = httpx.AsyncClient(timeout=10.0)
    crm_service = _build_crm_service(client=integration_client)
    alert_service = _build_alert_service(
        client=integration_client,
        business_config=runtime_config,
    )

    # Set up a voice AI pipeline using OpenAI, Cartesia, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=inference.STT(model="deepgram/nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    runtime_agent = build_runtime_agent(runtime_config)
    lifecycle = CallLifecycle(
        controller=runtime_agent,
        crm_service=crm_service,
        alert_service=alert_service,
        caller_id=_resolve_caller_id(ctx),
        logger=lifecycle_logger,
    )
    lifecycle.attach(session)

    integration_client_closed = False

    async def _close_integration_client(*_args: Any, **_kwargs: Any) -> None:
        nonlocal integration_client_closed
        if integration_client_closed:
            return

        integration_client_closed = True
        await integration_client.aclose()

    session.on("close", _close_integration_client)
    session.on("away", _close_integration_client)
    session.on("end", _close_integration_client)

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=build_runtime_agent(runtime_agent),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    await session.generate_reply()

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
