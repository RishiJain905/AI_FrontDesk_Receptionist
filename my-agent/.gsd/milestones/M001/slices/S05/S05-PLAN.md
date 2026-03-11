# S05: Call Lifecycle Orchestration and After-Hours Gate

**Goal:** Wire the real after-hours runtime lifecycle so the entrypoint can gate by configured local time, collect transcript and finalized call state, persist every complete or partial call through the CRM boundary, and send owner SMS alerts without one downstream failure blocking the other.
**Demo:** In unit/runtime-seam verification, the wired `src/agent.py` computes the after-hours decision in the configured timezone, starts the HVAC controller with an initial greeting, assembles a transcript from committed conversation events, finalizes exactly once on call close into a complete or partial `CallIntakeRecord` (including caller-ID fallback when no confirmed callback number exists), writes the record to CRM, sends SMS only when warranted, and exposes structured lifecycle diagnostics when CRM or SMS fail.

## Must-Haves

- `BusinessConfig` carries config-driven after-hours window fields and the demo config supplies the default overnight window (`17:00` → `09:00`) in `America/Toronto`; gate logic remains timezone-aware across midnight and surfaces a clear error when timezone data is unavailable.
- `CallIntakeRecord` can represent the R009 fallback-phone path explicitly by carrying caller ID and whether the callback number was confirmed, rather than hiding that distinction in free-form notes.
- `TranscriptAssembler` builds an ordered transcript from committed `conversation_item_added` events and ignores empty/noise-only entries so the finalized record and CRM note use durable conversation state.
- `CallLifecycle` finalizes exactly once, derives `call_status=complete|partial` from controller/task state, falls back to caller ID when the callback number was never confirmed, and builds a finalized record from controller diagnostics instead of duplicating slot logic.
- CRM and SMS are invoked independently through `CrmService` and `AlertService`; CRM failure never blocks SMS, SMS failure never blocks CRM, and `record.sms_sent` flips only after a successful alert send.
- Lifecycle observability is explicit: structured lifecycle status/log surfaces expose gate decision, transcript count, finalize phase, and provider outcomes using `IntegrationError.to_dict()`-style metadata without leaking secrets or raw transcript blobs.
- `src/agent.py` becomes the wired runtime entrypoint for S05: dotenv loading is explicit, after-hours gate/lifecycle/service composition is attached around `AgentSession`, and `session.generate_reply(...)` triggers the initial after-hours greeting after `session.start(...)`.
- Slice verification directly advances owned requirements R007 and R009 and supporting requirement R005, while keeping the config-driven contract aligned with R008.

## Proof Level

- This slice proves: operational
- Real runtime required: no
- Human/UAT required: no

## Verification

- `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`
- `uv run ruff check src/ tests/`

## Observability / Diagnostics

- Runtime signals: structured lifecycle diagnostics for `gate_checked`, `transcript_item_added`, `finalize_started`, `finalize_completed`, `crm_result`, and `sms_result`; deterministic `FinalClassification` / summary output stored on the finalized record.
- Inspection surfaces: `CallLifecycle.snapshot()` (or equivalent stable status surface), `tests/test_call_lifecycle.py`, `tests/test_after_hours_gate.py`, and `tests/test_agent.py` AST/runtime wiring assertions.
- Failure visibility: finalized status shows whether the call was complete or partial, which provider phase failed, whether caller-ID fallback was used, and whether finalization already ran, so duplicate-write or partial-call bugs localize quickly.
- Redaction constraints: lifecycle logs must reuse redacted integration error metadata and avoid dumping secrets, bearer/basic auth material, or full transcript bodies into log lines.

## Integration Closure

- Upstream surfaces consumed: `src/conversation/conversation_controller.py`, `src/conversation/intake_task.py`, `src/classification/live_classifier.py`, `src/services/crm/crm_service.py`, `src/services/alerts/alert_service.py`, `src/services/crm/ghl_service.py`, `src/services/alerts/sms_service.py`, `src/utils/errors.py`, and the shared HVAC type/config contracts.
- New wiring introduced in this slice: `src/orchestration/after_hours_gate.py`, `src/orchestration/call_lifecycle.py`, `src/orchestration/transcript_assembler.py`, `src/orchestration/summary_builder.py`, `src/classification/final_classifier.py`, `src/utils/time.py`, `src/utils/logging.py`, and `src/agent.py` session/lifecycle/greeting composition.
- What remains before the milestone is truly usable end-to-end: live GoHighLevel/Twilio credential proof, a real console/SIP demo, and the broader all-tests/ruff/README completion gate in S06.

## Tasks

- [x] **T01: Lock the S05 runtime boundary with failing gate, lifecycle, and entrypoint tests** `est:1h`
  - Why: S05 spans config, runtime events, partial-call failure handling, and real entrypoint composition; without a RED proof boundary it is too easy to ship only helper scaffolding instead of the promised operational lifecycle.
  - Files: `tests/test_after_hours_gate.py`, `tests/test_call_lifecycle.py`, `tests/test_agent.py`, `tests/test_types.py`
  - Do: Add pytest coverage that imports the planned S05 modules directly, proves overnight gate behavior at midnight-crossing boundaries, extends type tests for after-hours config plus caller-ID/phone-confirmation fields, and adds lifecycle tests with fake session/controller/service seams covering complete finalization, early-close partial finalization, caller-ID fallback, finalize-once idempotence, transcript assembly order, independent CRM/SMS failure handling, and diagnostic snapshot/log assertions. Update `tests/test_agent.py` to require the S05 entrypoint wiring: after-hours gate call, lifecycle construction/subscriptions, dotenv loading for both `.env.local` and `.env`, and an initial `session.generate_reply(...)` greeting trigger.
  - Verify: `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`
  - Done when: The named tests exist, collect cleanly, and fail only because the S05 runtime modules/contracts/wiring are not implemented yet.
- [x] **T02: Extend the config and record contracts and implement the timezone-safe after-hours gate** `est:1h15m`
  - Why: R007 and the R009 caller-ID fallback cannot be implemented honestly until the shared types/config expose the required time-window and phone-confirmation fields and the gate logic is pure, injectable, and correct across midnight.
  - Files: `src/hvac_types/business_config.py`, `src/hvac_types/call_intake_record.py`, `src/config/hvac_demo_config.py`, `src/config/load_config.py`, `src/utils/time.py`, `src/orchestration/after_hours_gate.py`, `tests/test_after_hours_gate.py`, `tests/test_types.py`
  - Do: Add config-driven after-hours start/end fields to `BusinessConfig` and the demo profile, add explicit caller-ID and callback-confirmation fields to `CallIntakeRecord`, extend config validation to reject blank/unparseable after-hours values, add timezone helpers that resolve `ZoneInfo` safely with a clear missing-tzdata failure message, and implement `is_after_hours(config, now=...)` / time-window parsing as pure helpers that correctly handle same-day and overnight windows.
  - Verify: `uv run pytest tests/test_after_hours_gate.py tests/test_types.py`
  - Done when: Gate tests pass at the documented overnight boundaries, type/config tests cover the new contract fields, and downstream lifecycle work can consume the pure gate/time helpers without additional config assumptions.
- [x] **T03: Build transcript assembly, final classification, and finalize-once call lifecycle orchestration** `est:1h30m`
  - Why: The slice’s core product increment is the post-call coordinator that turns controller state plus session events into a finalized record, not just isolated helpers.
  - Files: `src/orchestration/transcript_assembler.py`, `src/orchestration/summary_builder.py`, `src/classification/final_classifier.py`, `src/orchestration/call_lifecycle.py`, `src/utils/logging.py`, `src/orchestration/__init__.py`, `tests/test_call_lifecycle.py`
  - Do: Implement transcript assembly from committed conversation items, add a small typed final-classification surface plus deterministic summary builder, create `CallLifecycle` with explicit event subscription/finalize-once guards, derive complete vs partial status from controller/intake state, populate finalized `CallIntakeRecord` fields including caller-ID fallback and `notify_owner`, call CRM and SMS independently through the protocol boundaries, set `sms_sent` only after success, and expose a stable lifecycle snapshot/log surface that records provider outcomes and redacted failure metadata.
  - Verify: `uv run pytest tests/test_call_lifecycle.py`
  - Done when: Lifecycle tests prove transcript ordering, partial-call finalization, finalize-once behavior, caller-ID fallback semantics, CRM/SMS failure isolation, and diagnostic visibility from the stable snapshot/log surface.
- [x] **T04: Wire the S05 lifecycle into the real agent entrypoint and close the slice gate** `est:1h`
  - Why: S05 is not complete until the runnable entrypoint actually uses the gate and lifecycle orchestration around the real HVAC controller rather than leaving them as isolated test-only helpers.
  - Files: `src/agent.py`, `src/orchestration/call_lifecycle.py`, `src/orchestration/after_hours_gate.py`, `tests/test_agent.py`, `tests/test_call_lifecycle.py`
  - Do: Update `src/agent.py` to load `.env.local` and `.env` explicitly, build runtime service dependencies, compute/log the after-hours decision before session startup, instantiate and attach `CallLifecycle` around the `AgentSession`, preserve `build_runtime_agent()` as the controller factory seam, pass any available caller/session metadata into the lifecycle, trigger `session.generate_reply(...)` after `session.start(...)` for the inbound greeting, keep the outside-hours path as a logged graceful pass-through instead of a crash, and finish by running the full S05 pytest gate plus Ruff.
  - Verify: `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py && uv run ruff check src/ tests/`
  - Done when: The real entrypoint composes gate + lifecycle + greeting behavior, all S05 verification is green, and the runtime wiring is ready for S06’s broader full-suite/demo work.

## Files Likely Touched

- `src/agent.py`
- `src/hvac_types/business_config.py`
- `src/hvac_types/call_intake_record.py`
- `src/config/hvac_demo_config.py`
- `src/config/load_config.py`
- `src/utils/time.py`
- `src/utils/logging.py`
- `src/classification/final_classifier.py`
- `src/orchestration/after_hours_gate.py`
- `src/orchestration/call_lifecycle.py`
- `src/orchestration/transcript_assembler.py`
- `src/orchestration/summary_builder.py`
- `tests/test_after_hours_gate.py`
- `tests/test_call_lifecycle.py`
- `tests/test_agent.py`
- `tests/test_types.py`
