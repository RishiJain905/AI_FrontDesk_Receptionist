# Project

## What This Is

HVAC After-Hours Voice Intake Agent — a production-oriented voice AI agent built on LiveKit Cloud that answers a Canadian HVAC business phone line during after-hours (5 PM – 9 AM), captures structured caller intake details through adaptive slot-filling conversation, detects dangerous situations, classifies urgency in the background, writes structured records into GoHighLevel CRM, and sends SMS alerts when escalation rules match.

## Core Value

A caller phones after hours. The agent answers naturally, captures only the needed information, adapts if the caller already gave details, detects emergencies and safety hazards immediately, and ends cleanly — then writes the structured call record into GoHighLevel and alerts the owner when escalation rules match.

## Current State

M001 is in progress with **S01 and S02 complete**. The project now has both the HVAC contract layer and the adaptive intake/runtime proof boundary in place:

- `src/hvac_types/` package with classification enums, slot state types, `BusinessConfig`, and `CallIntakeRecord`
- `src/config/hvac_demo_config.py` default profile (`HVAC_DEMO_CONFIG`)
- `src/config/load_config.py` fail-fast required-field validation (`business_name`, `timezone`, `owner_phone`)
- `src/conversation/slot_tracker.py` and `src/conversation/intake_policy.py` for deterministic slot semantics and required-slot policy
- `src/classification/rules.py` and `src/classification/live_classifier.py` for config-driven live danger/urgency/category/address-relevance detection
- `src/conversation/intake_task.py` for tool-driven multi-turn intake with guarded completion
- proof coverage in `tests/test_types.py`, `tests/test_slot_filling.py`, and `tests/test_intake_task.py`

`src/agent.py` is still the generic LiveKit starter and the full HVAC conversation controller, safety handoff, CRM/SMS integrations, and after-hours orchestration remain for S03-S05.

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

- [ ] M001: HVAC After-Hours Voice Agent — In progress (S01-S02 complete): remaining work is safety-branch conversation control, GoHighLevel CRM integration, SMS alerting, after-hours gate/lifecycle wiring, and final demo readiness
