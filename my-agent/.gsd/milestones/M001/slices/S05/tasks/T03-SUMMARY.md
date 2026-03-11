---
id: T03
parent: S05
milestone: M001
provides:
  - Finalize-once call lifecycle orchestration with committed-event transcript assembly, deterministic final classification/summary derivation, and stable provider diagnostics snapshots
key_files:
  - src/orchestration/call_lifecycle.py
  - src/orchestration/transcript_assembler.py
  - src/classification/final_classifier.py
  - src/orchestration/summary_builder.py
  - src/utils/logging.py
key_decisions:
  - Added D035: finalization now uses committed conversation events plus controller diagnostics as the lifecycle source-of-truth, with redacted snapshot/log outputs
patterns_established:
  - Build finalized records from controller/task diagnostics + committed transcript, then run CRM and SMS independently with finalize-once idempotence
observability_surfaces:
  - CallLifecycle.snapshot()
  - structured lifecycle logs via utils.logging.log_lifecycle_event
  - redacted integration error payloads in crm_result/sms_result
duration: 1h20m
verification_result: passed
completed_at: 2026-03-11
blocker_discovered: false
---

# T03: Build transcript assembly, final classification, and finalize-once call lifecycle orchestration

**Implemented transcript assembly + finalization orchestration that finalizes once, persists provider outcomes independently, and exposes stable lifecycle diagnostics.**

## What Happened

Implemented the full T03 runtime surfaces and wired them together:

- Added `src/orchestration/transcript_assembler.py` with `TranscriptAssembler`/`TranscriptLine` to capture ordered committed `conversation_item_added` items from `user`/`assistant` roles, while ignoring non-message, interrupted, empty, and noise-only entries.
- Added `src/orchestration/summary_builder.py` with deterministic `build_final_summary(...)` and `build_ai_summary(...)` helpers derived from call status, controller intake state, and transcript excerpt.
- Added `src/classification/final_classifier.py` with a typed `FinalClassification` contract and default `FinalClassifier` that derives issue/urgency/danger from controller diagnostics and computes `notify_owner` without rerunning prompt-only logic.
- Added `src/utils/logging.py` with `get_logger`, structured `log_lifecycle_event`, and metadata redaction helpers.
- Implemented `src/orchestration/call_lifecycle.py` with:
  - explicit event subscription (`conversation_item_added`, `close`, `away`, `end`)
  - finalize-once guards + async lock
  - call status derivation (`complete` vs `partial`) from controller completion state
  - caller-ID fallback when callback number is unconfirmed
  - independent CRM and SMS provider calls with isolated failure capture
  - `sms_sent` mutation only after successful send
  - stable `snapshot()` surface containing finalized status, transcript count, provider outcomes, and a sanitized record snapshot.
- Updated exports in `src/classification/__init__.py` and `src/utils/__init__.py`.
- Marked T03 complete in the slice plan and appended decision D035 in `.gsd/DECISIONS.md`.

## Verification

Task-level verification required by T03:

- `uv run pytest tests/test_call_lifecycle.py` ✅ PASS (5/5)

Slice-level checks run per slice plan:

- `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`
  - `test_after_hours_gate` ✅
  - `test_call_lifecycle` ✅
  - `test_types` ✅
  - `test_agent` ❌ (2 expected REDs for pending T04 wiring: missing `.env` load and missing after-hours/lifecycle composition in `src/agent.py`)
- `uv run ruff check src/ tests/` ✅ PASS

## Diagnostics

How to inspect this boundary later:

- `CallLifecycle.snapshot()` exposes stable finalized state:
  - `finalized`, `finalize_attempts`, `call_status`, `transcript_count`, `caller_id_fallback_used`, `crm_result`, `sms_result`, and sanitized `record`
- Structured lifecycle logs are emitted via `log_lifecycle_event(...)` for:
  - `transcript_item_added`, `finalize_started`, `crm_result`, `sms_result`, `finalize_completed`
- Provider failures in snapshot/log surfaces include typed redacted metadata (`service`, `operation`, `status_code`, `detail`) without leaking bearer/basic/auth tokens or raw transcript bodies.

## Deviations

- None.

## Known Issues

- `tests/test_agent.py` remains RED until T04 entrypoint wiring is implemented.

## Files Created/Modified

- `src/orchestration/transcript_assembler.py` — committed event transcript builder with noise/interruption filtering
- `src/orchestration/summary_builder.py` — deterministic summary + ai-summary helpers
- `src/classification/final_classifier.py` — typed final classification derivation surface
- `src/utils/logging.py` — structured lifecycle logger + metadata redaction utilities
- `src/orchestration/call_lifecycle.py` — finalize-once lifecycle orchestration, provider isolation, snapshot diagnostics
- `src/classification/__init__.py` — exports final classifier types
- `src/utils/__init__.py` — exports lifecycle logging helpers
- `.gsd/DECISIONS.md` — appended D035 lifecycle source-of-truth/observability decision
- `.gsd/milestones/M001/slices/S05/S05-PLAN.md` — marked T03 `[x]`
