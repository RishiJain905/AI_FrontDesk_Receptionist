# Project

## What This Is

HVAC After-Hours Voice Intake Agent — a production-oriented voice AI agent built on LiveKit Cloud that answers a Canadian HVAC business phone line during after-hours (5 PM – 9 AM), captures structured caller intake details through adaptive slot-filling conversation, detects dangerous situations, classifies urgency in the background, writes structured records into GoHighLevel CRM, and sends SMS alerts when escalation rules match.

## Core Value

A caller phones after hours. The agent answers naturally, captures only the needed information, adapts if the caller already gave details, detects emergencies and safety hazards immediately, and ends cleanly — then writes the structured call record into GoHighLevel and alerts the owner when escalation rules match.

## Current State

M001 is in progress with **S01, S02, S03, and S04 complete**. The project now has the HVAC contract layer, deterministic adaptive intake runtime, the real after-hours conversation controller, and provider-backed CRM/SMS integration boundaries in place:

- `src/hvac_types/` package with classification enums, slot state types, `BusinessConfig`, and enriched `CallIntakeRecord` finalized-call fields
- `src/config/hvac_demo_config.py` default profile (`HVAC_DEMO_CONFIG`)
- `src/config/load_config.py` fail-fast required-field validation (`business_name`, `timezone`, `owner_phone`)
- `src/conversation/slot_tracker.py` and `src/conversation/intake_policy.py` for deterministic slot semantics and required-slot policy
- `src/classification/rules.py` and `src/classification/live_classifier.py` for config-driven live danger/urgency/category/address-relevance detection
- `src/conversation/intake_task.py` for tool-driven multi-turn intake with guarded completion
- `src/conversation/prompts.py` for deterministic after-hours/safety/closing prompt surfaces
- `src/conversation/conversation_controller.py` for `HVACConversationController`, `HVACIntakeAgent`, `SafetyAgent`, explicit danger handoff, and inspectable controller diagnostics
- `src/services/crm/` with `CrmService`, deterministic GoHighLevel mappers, and `GoHighLevelService` search/create/update/note flow
- `src/services/alerts/` with `AlertService`, concise owner-alert formatting, and `TwilioSmsService` send/skip/error handling
- `src/utils/phone.py` and `src/utils/errors.py` for shared number normalization and redacted typed integration diagnostics
- `src/agent.py` now composes the validated HVAC controller through `build_runtime_agent()` instead of the generic starter assistant
- proof coverage in `tests/test_types.py`, `tests/test_slot_filling.py`, `tests/test_intake_task.py`, `tests/test_prompts.py`, `tests/test_conversation_controller.py`, `tests/test_agent.py`, `tests/test_ghl_service.py`, `tests/test_sms_service.py`, and `tests/test_phone_utils.py`

Remaining milestone work is S05-S06: after-hours gate/lifecycle orchestration, transcript/finalization wiring, real end-to-end call persistence/alert execution, and full demo hardening.

## Architecture / Key Patterns

- Python, LiveKit Agents SDK ~1.4 with LiveKit Inference
- Single `src/agent.py` entrypoint (required by Dockerfile)
- Additional modules under `src/` alongside agent.py
- AgentTask pattern for structured slot collection (LiveKit's task/workflow API)
- Agent handoff for safety branch (interrupt normal intake, switch to SafetyAgent)
- Background asyncio tasks for live classification and post-call CRM/SMS writes
- Config-driven business settings (no hardcoded HVAC values in core logic)
- Integration failures isolated — CRM/SMS errors do not crash the voice session
- uv package manager; tests via pytest with pytest-asyncio

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: HVAC After-Hours Voice Agent — In progress (S01-S04 complete): remaining work is after-hours gate/lifecycle wiring, transcript/finalization flow, operational CRM/SMS proof, and final demo readiness
