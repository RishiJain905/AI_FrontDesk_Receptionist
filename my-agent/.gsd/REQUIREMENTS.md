# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

### R001 — After-Hours Voice Intake
- Class: primary-user-loop
- Status: active
- Description: Agent answers calls during the 5 PM – 9 AM window, captures caller name, callback number, issue summary, best callback time, and conditionally captures service address — producing a `CallIntakeRecord` for every call including partial ones.
- Why it matters: This is the entire product loop. Without it nothing else matters.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S01, M001/S02
- Validation: `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_agent.py tests/test_intake_task.py` — proves the HVAC controller opens as the after-hours line, continues adaptive intake through `IntakeTask`, and closes only after required details are captured
- Notes: Slot-filling must not over-skip on weak extraction; confirmation required for tentative slots.

### R002 — Adaptive Slot-Filling Conversation
- Class: core-capability
- Status: active
- Description: Conversation is slot-based (missing / tentative / confirmed states) not a fixed script. Agent asks only for missing info, confirms tentative info, and adapts to however much the caller volunteered up front.
- Why it matters: Makes the agent feel natural and not robotic; prevents duplicate questions on already-confirmed details.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S03
- Validation: `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` — proves SlotTracker state transitions, required-slot completion guards, adaptive multi-turn intake, and explicit confirmation of tentative values before completion
- Notes: Critical skip rule — must not close early unless all required slots are confirmed.

### R003 — Safety / Emergency Branch
- Class: core-capability
- Status: active
- Description: When danger signals (gas smell, CO, smoke, electrical burning, flooding, sparking) are detected live during the call, the agent immediately switches to safety-first behavior: calm guidance, emergency services advice, minimum viable data capture, sets dangerDetected=true, notifyOwner=true.
- Why it matters: Safety-critical path; must override all other intake logic. Failure here is a liability.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S01, M001/S02
- Validation: `uv run pytest tests/test_conversation_controller.py` — proves danger keywords trigger an explicit LiveKit `agent_handoff` to `SafetyAgent` and a safety-first reply with emergency guidance before minimal intake capture
- Notes: Safety must interrupt the normal intake flow, not wait for it to finish.

### R004 — Background Classification
- Class: core-capability
- Status: active
- Description: Live classification runs during the call to detect danger early and adapt behavior. Final classification post-call assigns issueCategory, urgencyLevel, urgencyReason, aiSummary, notifyOwner.
- Why it matters: Callers should not be asked to select from a tier menu; inference must happen in the background.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S04
- Validation: `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` — proves deterministic live danger/urgency/category/address-relevance classification and its use inside the intake task boundary
- Notes: Classification must not live only in prompt text — must be implemented as code logic.

### R005 — GoHighLevel CRM Integration
- Class: integration
- Status: active
- Description: Every call (complete or partial) writes a structured record to GoHighLevel: find/create contact by phone, attach intake fields (urgency, category, callback time, customer type, danger flag), attach transcript, attach AI summary.
- Why it matters: The entire intake product is worthless if no record is written. CRM write is the delivery mechanism.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: M001/S05
- Validation: `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py` — proves deterministic GoHighLevel contact payload mapping, exact normalized-phone create/update decisions, structured note attachment, and typed CRM failure diagnostics via mock HTTP transport
- Notes: CRM failures must not crash the voice session. Log clearly for retry.

### R006 — SMS Owner Alert
- Class: integration
- Status: active
- Description: When notifyOwner=true, sends a concise SMS alert to the configured owner phone with caller name, number, issue summary, and urgency level.
- Why it matters: Owner needs to know about urgent and safety-critical calls immediately after hours.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py` — proves concise owner-alert formatting, notify_owner/sms_sent skip rules, Twilio Basic Auth form-post request shape, and typed SMS failure diagnostics via mock HTTP transport
- Notes: SMS failure must not block CRM write. No duplicate alerts per finalized call.

### R007 — After-Hours Gate
- Class: core-capability
- Status: active
- Description: The agent is active only between 5 PM and 9 AM in the configured timezone (default: America/Toronto). Outside this window the gate is a no-op or graceful pass-through.
- Why it matters: The system is specifically an after-hours handler; activating during business hours would conflict with live staff.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: `uv run pytest tests/test_after_hours_gate.py tests/test_agent.py tests/test_types.py` — proves timezone-safe same-day/overnight gate math (including midnight boundaries), strict config window validation, and real entrypoint gate wiring with graceful outside-hours behavior
- Notes: Time comparison must be timezone-aware and correct across midnight (overnight window spanning two calendar days).

### R008 — Config-Driven Business Settings
- Class: quality-attribute
- Status: active
- Description: All business-specific values (business name, timezone, hours, emergency keywords, urgent keywords, owner alert phone, safety message, issue categories) come from a BusinessConfig object loaded from a config file plus environment overrides — never hardcoded in core logic.
- Why it matters: Makes the engine reusable for any HVAC business without touching core logic.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: all
- Validation: `uv run pytest tests/test_types.py` (TestBusinessConfig, TestLoadConfig) — partial proof of config contract and boot-time required-field validation
- Notes: S01 proves typed config + fail-fast required fields; env overrides and downstream runtime wiring remain for later slices.

### R009 — Graceful Failure Handling
- Class: failure-visibility
- Status: active
- Description: Early hang-ups produce partial CallIntakeRecords with callStatus=partial. CRM failures are logged but do not crash the session. SMS failures do not block CRM. Silence/bad recognition re-prompts briefly then ends gracefully. Missing callback number falls back to callerId with confirmed=false.
- Why it matters: After-hours calls are high-stakes; a crash or silent failure means a lost lead and no record.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: M001/S04
- Validation: `uv run pytest tests/test_call_lifecycle.py tests/test_agent.py` — proves partial finalization, finalize-once idempotence, caller-ID fallback with `callback_number_confirmed=false`, and CRM/SMS failure isolation during runtime wiring
- Notes: Finalization must be idempotent where practical.

### R010 — Test Coverage
- Class: quality-attribute
- Status: active
- Description: Every major agent behavior path has at least one pytest test using LiveKit's AgentSession eval framework: normal intake, safety branch trigger, partial call, missing fields, CRM write, SMS send logic.
- Why it matters: Voice agents are notoriously hard to verify manually; silent regressions from prompt or model changes are the main failure mode.
- Source: inferred (from AGENTS.md TDD requirement and livekit-agents skill)
- Primary owning slice: M001/S06
- Supporting slices: all
- Validation: `uv run pytest tests/test_s06_readiness.py tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider && uv run pytest && uv run ruff check src/ && uv run ruff format --check src/` — proves readiness artifacts stay enforced, the full 131-test behavior matrix (normal intake, safety branch, partial call, missing fields, CRM write, SMS logic, gate/failure isolation) remains green, and source-quality gates are repeatably clean at slice closure
- Notes: Full S06 closure also requires source-quality gates (`uv run ruff check src/`, `uv run ruff format --check src/`) alongside the pytest evidence above.

## Deferred

### R020 — Email Alerts
- Class: integration
- Status: deferred
- Description: Email notification to owner on escalated calls.
- Why it matters: Additional notification channel.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly out of scope for V1 per spec section 3.

### R021 — Multilingual Support
- Class: core-capability
- Status: deferred
- Description: Agent handles non-English callers.
- Why it matters: Canadian market has French-speaking callers.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly deferred for V1 per spec section 3.

### R022 — Appointment Scheduling
- Class: core-capability
- Status: deferred
- Description: Agent books service appointments directly.
- Why it matters: Would complete the customer journey in-call.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Out of scope V1 per spec section 3.

## Out of Scope

### R030 — FAQ Answering
- Class: anti-feature
- Status: out-of-scope
- Description: Agent answering broad business FAQs (pricing, warranties, policies).
- Why it matters: Prevents scope creep into a general chatbot.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Explicitly excluded per spec section 3 and product rules.

### R031 — Dispatch Orchestration
- Class: anti-feature
- Status: out-of-scope
- Description: Agent dispatching or routing technicians.
- Why it matters: Out of scope V1.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Explicitly excluded per spec section 3.

### R032 — Admin Dashboard / Multi-Tenant UI
- Class: anti-feature
- Status: out-of-scope
- Description: Owner-facing web UI for reviewing calls, managing tenants.
- Why it matters: Not needed for V1 demo.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Explicitly excluded per spec section 3.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | primary-user-loop | active | M001/S03 | S01, S02 | `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_agent.py tests/test_intake_task.py` — after-hours HVAC greeting, adaptive intake continuation through the controller, and clean close after required slot capture |
| R002 | core-capability | active | M001/S02 | S03 | `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` — slot-state semantics, adaptive multi-turn collection, tentative confirmation, guarded completion |
| R003 | core-capability | active | M001/S03 | S01, S02 | `uv run pytest tests/test_conversation_controller.py` — explicit safety handoff event plus emergency-first guidance on danger keywords |
| R004 | core-capability | active | M001/S02 | S04 | `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` — deterministic live classification for danger, urgency, category, and address relevance |
| R005 | integration | active | M001/S04 | S05 | `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py` — deterministic GoHighLevel contact upsert/note attachment with exact normalized-phone matching and typed CRM failure diagnostics |
| R006 | integration | active | M001/S04 | none | `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py` — concise Twilio owner alert send/skip behavior, Basic Auth request shape, and typed SMS failure diagnostics |
| R007 | core-capability | active | M001/S05 | none | `uv run pytest tests/test_after_hours_gate.py tests/test_agent.py tests/test_types.py` — timezone-safe gate math across midnight, strict after-hours config validation, and entrypoint gate wiring |
| R008 | quality-attribute | active | M001/S01 | all | `tests/test_types.py` config contract + loader validation (partial) |
| R009 | failure-visibility | active | M001/S05 | S04 | `uv run pytest tests/test_call_lifecycle.py tests/test_agent.py` — partial-call finalize path, caller-ID fallback semantics, finalize-once guard, and CRM/SMS failure isolation |
| R010 | quality-attribute | active | M001/S06 | all | `uv run pytest tests/test_s06_readiness.py tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider && uv run pytest && uv run ruff check src/ && uv run ruff format --check src/` — readiness-contract tests + full-suite pass + source-quality gates provide repeatable S06 closure evidence |
| R020 | integration | deferred | none | none | unmapped |
| R021 | core-capability | deferred | none | none | unmapped |
| R022 | core-capability | deferred | none | none | unmapped |
| R030 | anti-feature | out-of-scope | none | none | n/a |
| R031 | anti-feature | out-of-scope | none | none | n/a |
| R032 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 10
- Mapped to slices: 10
- Validated: 9
- Unmapped active requirements: 0
