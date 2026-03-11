---
id: T01
parent: S05
milestone: M001
provides:
  - RED proof boundary tests for S05 gate math, lifecycle orchestration, runtime entrypoint wiring, and shared type-contract expansion.
key_files:
  - tests/test_after_hours_gate.py
  - tests/test_call_lifecycle.py
  - tests/test_agent.py
  - tests/test_types.py
  - .gsd/milestones/M001/slices/S05/S05-PLAN.md
  - .gsd/STATE.md
key_decisions:
  - The S05 RED boundary imports planned runtime modules directly (`orchestration.*`, `classification.final_classifier`, `utils.time`, `utils.logging`) so missing implementation fails honestly at collection time.
patterns_established:
  - Lifecycle proof tests use fake session/controller/service seams to enforce finalize-once behavior, caller-ID fallback semantics, provider isolation, and snapshot-based diagnostics.
observability_surfaces:
  - `tests/test_after_hours_gate.py`, `tests/test_call_lifecycle.py`, `tests/test_agent.py`, and `tests/test_types.py` assertions over gate decisions, lifecycle `snapshot()` metadata, and entrypoint AST wiring.
duration: 55m
verification_result: passed
completed_at: 2026-03-11 19:28 EDT
blocker_discovered: false
---

# T01: Lock the S05 runtime boundary with failing gate, lifecycle, and entrypoint tests

**Added the full S05 RED test boundary so missing gate/lifecycle/runtime wiring now fails in targeted, diagnosable ways before implementation.**

## What Happened

I implemented the T01 RED contract exactly around the four required test surfaces:

- Created `tests/test_after_hours_gate.py` with direct imports of `orchestration.after_hours_gate` and `utils.time`, plus coverage for:
  - same-day and overnight windows
  - midnight-crossing behavior in `America/Toronto`
  - injectable `now` usage
  - invalid/missing timezone error path via typed timezone-resolution failures
- Created `tests/test_call_lifecycle.py` with direct imports of `orchestration.call_lifecycle`, `classification.final_classifier`, and `utils.logging`, then added fake seams for controller/session/CRM/SMS to assert:
  - ordered transcript assembly from committed items
  - complete vs partial finalization
  - R009 fallback phone semantics (`phone_number` falls back to caller ID, `callback_number_confirmed=False`)
  - finalize-once idempotence on duplicate close events
  - CRM/SMS failure isolation and stable snapshot diagnostics with structured error metadata
- Updated `tests/test_agent.py` AST runtime-wiring checks to require:
  - explicit dotenv loading for both `.env.local` and `.env`
  - import/call of `is_after_hours`
  - `CallLifecycle` construction + session-event subscription seam
  - awaited `session.generate_reply(...)` after awaited `session.start(...)`
- Extended `tests/test_types.py` shared contract tests so they fail until:
  - `BusinessConfig` exposes `after_hours_start` and `after_hours_end`
  - demo config defines the default `17:00` → `09:00` window
  - `CallIntakeRecord` exposes `caller_id` and `callback_number_confirmed`

I then marked T01 complete in `.gsd/milestones/M001/slices/S05/S05-PLAN.md` and updated `.gsd/STATE.md` for the next task.

## Verification

Ran required slice checks:

- `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`
  - **Result:** FAIL (expected RED). Current failures are missing S05 runtime modules:
    - `ModuleNotFoundError: orchestration`
    - `ModuleNotFoundError: classification.final_classifier`
- `uv run ruff check src/ tests/`
  - **Result:** PASS (`All checks passed!`)

Additional localization run to verify non-collection RED assertions are targeted to S05 scope:

- `uv run pytest tests/test_agent.py tests/test_types.py`
  - **Result:** 7 failed / 50 passed
  - Failures are the intended missing S05 contracts/wiring (`.env` load, gate/lifecycle imports, after-hours config fields, caller-ID/confirmation fields).

## Diagnostics

To inspect this boundary later:

- Run `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`.
- If collection fails, missing modules are in S05 implementation scope (`orchestration.*`, `classification.final_classifier`, `utils.*`).
- If collection passes later, assertion failures localize quickly by file:
  - `test_after_hours_gate` → gate math/timezone handling
  - `test_call_lifecycle` → transcript/finalize/provider diagnostics semantics
  - `test_agent` → entrypoint wiring order/composition
  - `test_types` → shared contract shape for config/record fields

## Deviations

- None.

## Known Issues

- None beyond the expected RED failures for unimplemented S05 runtime modules/contracts/wiring.

## Files Created/Modified

- `tests/test_after_hours_gate.py` — new RED tests for timezone-safe gate behavior and timezone error handling.
- `tests/test_call_lifecycle.py` — new RED lifecycle orchestration tests with fake seams and diagnostic assertions.
- `tests/test_agent.py` — expanded AST runtime-wiring assertions for dotenv, gate/lifecycle composition, and post-start greeting.
- `tests/test_types.py` — extended contract assertions for after-hours config fields and caller-ID/callback-confirmation record fields.
- `.gsd/milestones/M001/slices/S05/S05-PLAN.md` — marked T01 as complete (`[x]`).
- `.gsd/STATE.md` — updated active state to reflect T01 completion and T02 next action.
