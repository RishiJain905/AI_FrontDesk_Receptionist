# M001: HVAC After-Hours Voice Agent

**Vision:** Transform the generic LiveKit starter into a production-oriented HVAC after-hours intake agent that captures caller details via adaptive slot-filling conversation, detects safety emergencies, writes every call to GoHighLevel CRM, and sends SMS alerts when escalation rules match.

## Success Criteria

- Caller phones after hours; agent greets naturally, identifies as after-hours assistant, collects name / callback number / issue summary / callback time adaptively — asking only for missing/tentative info
- Caller mentions a danger signal (gas smell, CO, burning) and agent immediately switches to safety branch, provides calm emergency guidance, still attempts minimum viable data capture
- Every completed or partial call produces a `CallIntakeRecord` persisted to GoHighLevel with transcript, AI summary, and structured fields
- SMS alert is sent to the owner phone when notifyOwner=true; no SMS is sent for standard-urgency calls
- After-hours gate is accurate across midnight in America/Toronto timezone
- All major behavioral paths have passing pytest tests

## Key Risks / Unknowns

- GoHighLevel v2 API payload shape — contact upsert field names and note/activity attachment endpoint
- AgentTask + session.update_agent mid-call handoff confirmed working in livekit-agents~=1.4
- Slot-filling via function_tool pattern — need to confirm tool-call reliability for structured extraction
- zoneinfo vs pytz for overnight timezone-aware window comparison

## Proof Strategy

- GoHighLevel payload shape → retire in S04 by writing a real contact and note with test credentials and observing the GHL contact record
- AgentTask + handoff mid-call → retire in S03 by testing safety branch handoff with AgentSession eval; handoff event must be asserted
- Slot-filling function_tool reliability → retire in S02 by running multi-turn eval tests that verify slots fill correctly and tentative slots get confirmed
- Overnight timezone comparison → retire in S05 by unit-testing the gate at boundary times around midnight in America/Toronto

## Verification Classes

- Contract verification: pytest AgentSession evals for conversation behavior; unit tests for slot tracker, classifier, and after-hours gate
- Integration verification: real GoHighLevel API call creating/updating a contact with note and transcript; real SMS send to owner phone
- Operational verification: full call lifecycle run to completion without crash; partial call (early hangup) still writes to CRM
- UAT / human verification: demo call via LiveKit console or SIP; human confirms CRM record and SMS received

## Milestone Definition of Done

This milestone is complete only when all are true:

- All 6 slices are complete with passing tests
- `src/agent.py` entrypoint runs `uv run python src/agent.py console` and behaves as the HVAC agent
- Safety branch triggers immediately on danger keywords in a test run
- GoHighLevel integration creates real contacts (verified with test credentials)
- SMS integration sends real alerts (verified with Twilio test credentials or equivalent)
- After-hours gate tests pass at midnight-crossing boundary
- `uv run pytest` passes with no failures
- `uv run ruff check src/` and `uv run ruff format --check src/` pass

## Requirement Coverage

- Covers: R001, R002, R003, R004, R005, R006, R007, R008, R009, R010
- Partially covers: none
- Leaves for later: R020 (email), R021 (multilingual), R022 (scheduling)
- Orphan risks: none

## Slices

- [x] **S01: Core Types, Config, and Data Model** `risk:low` `depends:[]`
  > After this: The full data contract (`CallIntakeRecord`, `BusinessConfig`, slot types, classification types) and `hvac_demo_config.py` exist and are importable; config loader validates required fields.

- [x] **S02: Slot-Filling Intake and Background Classification** `risk:high` `depends:[S01]`
  > After this: `IntakeTask` (AgentTask) collects all required slots adaptively via function tools; slot tracker correctly transitions missing→tentative→confirmed; live classifier detects danger and urgency signals; eval tests prove multi-turn slot filling works and tentative slots get confirmed.

- [x] **S03: Conversation Controller, Prompts, and Safety Branch** `risk:high` `depends:[S02]`
  > After this: Full conversation runs end-to-end in console mode: opening greeting, adaptive intake, safety branch handoff when danger detected, clean call closing; eval tests assert safety handoff triggers on danger keywords.

- [x] **S04: GoHighLevel CRM and SMS Alert Integrations** `risk:medium` `depends:[S01]`
  > After this: `GoHighLevelService` creates/updates contacts and attaches structured notes; `SmsService` sends concise owner alerts; both are isolated from each other's failures; integration tests assert correct payload shape (can use mock HTTP for CI).

- [x] **S05: Call Lifecycle Orchestration and After-Hours Gate** `risk:medium` `depends:[S02,S03,S04]`
  > After this: Full call lifecycle runs start-to-finish: after-hours gate → intake → finalize → CRM write → SMS if needed; partial calls (hang-up) produce callStatus=partial records; after-hours gate unit tests pass at midnight-crossing boundaries; `src/agent.py` is the wired entrypoint.

- [ ] **S06: Full Test Suite and Demo Readiness** `risk:low` `depends:[S05]`
  > After this: `uv run pytest` passes all tests covering: normal intake, partial call, safety branch, no-heat urgency, missing fields, outside-hours gate, CRM failure isolation, SMS failure isolation; ruff checks pass; README updated with usage instructions.

## Boundary Map

### S01 → S02

Produces:
- `src/config/hvac_demo_config.py` — `HVAC_DEMO_CONFIG: BusinessConfig` instance
- `src/config/load_config.py` — `load_config() -> BusinessConfig` (validates required fields)
- `src/types/call_intake_record.py` — `CallIntakeRecord` dataclass
- `src/types/business_config.py` — `BusinessConfig` dataclass
- `src/types/slot_state.py` — `SlotStatus` enum (MISSING / TENTATIVE / CONFIRMED), `SlotState` dataclass
- `src/types/classification.py` — `IssueCategory`, `UrgencyLevel`, `DangerType` enums

Consumes:
- nothing (first slice)

### S01 → S04

Produces:
- `CallIntakeRecord` — consumed by CRM mapper and SMS formatter
- `BusinessConfig` — consumed by CRM service (owner phone) and SMS service

### S02 → S03

Produces:
- `src/conversation/slot_tracker.py` — `SlotTracker` class managing all slot transitions; `get_missing_slots()`, `get_tentative_slots()`, `update_slot()`, `all_required_confirmed()`
- `src/conversation/intake_policy.py` — `IntakePolicy`: which fields required vs conditional, address relevance logic, danger-mode minimum viable fields
- `src/classification/live_classifier.py` — `LiveClassifier`: `analyze(transcript_so_far, config) -> LiveClassification` (dangerDetected, likely urgency, address_relevant, customer_type_hint)
- `src/classification/rules.py` — `keyword_matches(text, keywords)`, `DANGER_CATEGORIES`, safety override logic
- `IntakeTask(AgentTask)` — AgentTask subclass with function tools for slot recording; completes when all required slots confirmed

Consumes from S01:
- `SlotStatus`, `SlotState`, `BusinessConfig`, `CallIntakeRecord` types
- `HVAC_DEMO_CONFIG`

### S02 → S05

Produces:
- `IntakeTask` — started by call lifecycle
- `LiveClassifier` — used during call to update `CallIntakeRecord` incrementally

### S03 → S05

Produces:
- `src/conversation/prompts.py` — `build_system_prompt(config)`, `SAFETY_INSTRUCTIONS`, `CLOSING_INSTRUCTIONS`
- `src/conversation/conversation_controller.py` — `HVACIntakeAgent(Agent)` and `SafetyAgent(Agent)`; opening prompt behavior; handoff to `SafetyAgent` when danger detected
- `HVACIntakeAgent` — main agent class wired to `IntakeTask`
- `SafetyAgent` — safety branch agent; minimal intake + serious calm guidance

Consumes from S02:
- `IntakeTask`, `SlotTracker`, `IntakePolicy`, `LiveClassifier`

### S04 → S05

Produces:
- `src/services/crm/crm_service.py` — `CrmService` protocol: `upsert_contact(record)`, `attach_call_note(contact_id, record)`
- `src/services/crm/ghl_service.py` — `GoHighLevelService(CrmService)` implementing GHL v2 API
- `src/services/crm/mappers.py` — `to_ghl_contact(record)`, `to_ghl_note(record)` payload builders
- `src/services/alerts/alert_service.py` — `AlertService` protocol: `send_owner_sms(record)`
- `src/services/alerts/sms_service.py` — `TwilioSmsService(AlertService)` with Twilio REST
- `src/utils/phone.py` — `normalize_phone(number) -> str`
- `src/utils/errors.py` — `IntegrationError`, `CrmError`, `SmsError`

Consumes from S01:
- `CallIntakeRecord`, `BusinessConfig`

### S05 → S06

Produces:
- `src/orchestration/after_hours_gate.py` — `is_after_hours(config) -> bool` (timezone-safe overnight)
- `src/orchestration/call_lifecycle.py` — `CallLifecycle`: coordinates start, in-call updates, finalize, CRM write, SMS send
- `src/orchestration/transcript_assembler.py` — `TranscriptAssembler`: builds transcript from `conversation_item_added` events
- `src/orchestration/summary_builder.py` — `build_summary(record) -> str`
- `src/classification/final_classifier.py` — `FinalClassifier.classify(record, transcript, config) -> FinalClassification`
- `src/utils/time.py` — `now_in_timezone(tz)`, `parse_time_window(start, end, tz)`
- `src/utils/logging.py` — structured logger setup
- Updated `src/agent.py` — full wired entrypoint

Consumes from S02, S03, S04:
- All of the above modules
