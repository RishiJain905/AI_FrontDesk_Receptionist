---
estimated_steps: 5
estimated_files: 7
---

# T03: Build transcript assembly, final classification, and finalize-once call lifecycle orchestration

**Slice:** S05 — Call Lifecycle Orchestration and After-Hours Gate
**Milestone:** M001

## Description

Implement the operational heart of S05: turn session events plus controller state into a finalized `CallIntakeRecord`, persist it through the provider protocols, and expose enough stable diagnostics that a future agent can understand partial/failure outcomes without replaying a whole call.

## Steps

1. Add `src/orchestration/transcript_assembler.py` to capture ordered user/assistant transcript lines from committed `conversation_item_added` events while ignoring empty or interrupted/noise-only items.
2. Add `src/classification/final_classifier.py` and `src/orchestration/summary_builder.py` with a small typed final-classification surface that derives urgency, danger, notify-owner, and summary fields from controller/intake state plus transcript without re-running prompt-only logic.
3. Add `src/utils/logging.py` to centralize a structured lifecycle logger shape that records gate/finalize/provider phases using redacted metadata only.
4. Implement `src/orchestration/call_lifecycle.py` with explicit event subscription, finalize-once guards, record-building from controller diagnostics, caller-ID fallback semantics, CRM+SMS independence, `sms_sent` mutation only after success, and a stable `snapshot()`/status surface for tests.
5. Run `tests/test_call_lifecycle.py` until it passes, tightening the lifecycle state surface rather than weakening the failure-path assertions.

## Must-Haves

- [ ] Transcript assembly uses committed session events as the authoritative source, not prompt text or ad hoc controller strings.
- [ ] Finalization is idempotent: multiple close/away/end signals cannot double-write CRM notes or duplicate owner alerts.
- [ ] CRM and SMS are called independently through their protocols, and typed integration failures are logged/exposed with stable metadata.
- [ ] The lifecycle exposes a stable snapshot/status surface future agents can inspect after success or failure.

## Verification

- `uv run pytest tests/test_call_lifecycle.py`
- Expected result: PASS, proving transcript capture, final-record assembly, partial-call handling, failure isolation, and lifecycle diagnostics.

## Observability Impact

- Signals added/changed: Structured lifecycle phase/result events plus a stable in-memory snapshot surface for finalized status, transcript count, and provider outcomes.
- How a future agent inspects this: Use `CallLifecycle.snapshot()` in tests/debugging and capture the structured logger output for provider/gate/finalize phases.
- Failure state exposed: Duplicate finalization attempts, CRM write failure, SMS failure, and caller-ID fallback are all visible without inspecting raw HTTP payloads or replaying the call.

## Inputs

- `src/conversation/conversation_controller.py` — authoritative controller diagnostics (`current_mode`, `latest_classification`, `handoff_state`, `last_completed_intake_summary`).
- `src/conversation/intake_task.py` — structured completion semantics and slot snapshot shape.
- `src/services/crm/crm_service.py`, `src/services/alerts/alert_service.py`, and `src/utils/errors.py` — protocol/error boundaries S05 must reuse rather than bypass.
- `tests/test_call_lifecycle.py` — RED orchestration contract from T01.

## Expected Output

- `src/orchestration/transcript_assembler.py` — committed-message transcript builder.
- `src/classification/final_classifier.py` — typed final-classification surface used during finalization.
- `src/orchestration/summary_builder.py` — deterministic finalized summary builder.
- `src/orchestration/call_lifecycle.py` — finalize-once coordinator with provider isolation and diagnostics.
