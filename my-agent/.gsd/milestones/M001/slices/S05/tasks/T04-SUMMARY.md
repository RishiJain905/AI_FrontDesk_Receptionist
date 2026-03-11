---
id: T04
parent: S05
milestone: M001
provides:
  - Real runtime entrypoint composition for S05 with explicit dotenv loading, after-hours gate evaluation, lifecycle wiring, and initial greeting trigger
key_files:
  - src/agent.py
  - .gsd/milestones/M001/slices/S05/S05-PLAN.md
  - .gsd/DECISIONS.md
key_decisions:
  - Added D036: entrypoint now composes real GoHighLevel/Twilio providers when configured and protocol-compatible no-op fallbacks when secrets are absent so lifecycle wiring stays runnable in local/dev
patterns_established:
  - Build one runtime controller instance, attach CallLifecycle to the session before start, and pass the same controller into session.start via build_runtime_agent(...) seam
observability_surfaces:
  - structured lifecycle logs via gate_checked + lifecycle phases
  - tests/test_agent.py AST wiring assertions
  - CallLifecycle.snapshot() status surface
duration: 1h
verification_result: passed
completed_at: 2026-03-11
blocker_discovered: false
---

# T04: Wire the S05 lifecycle into the real agent entrypoint and close the slice gate

**Implemented the real S05 runtime composition in `src/agent.py`, including gate/lifecycle/service wiring and startup greeting generation, and closed the slice verification gate.**

## What Happened

Implemented the T04 entrypoint wiring contract end-to-end in `src/agent.py`:

- Added explicit dotenv boot loading for both `.env.local` and `.env`.
- Imported and invoked `is_after_hours(...)` in the real runtime entrypoint, then emitted structured `gate_checked` diagnostics with redacted metadata support via `log_lifecycle_event(...)`.
- Added an explicit outside-hours branch that logs a graceful pass-through message instead of crashing.
- Built runtime integration dependencies in entrypoint composition:
  - real `GoHighLevelService` and `TwilioSmsService` when required env vars are present
  - protocol-compatible no-op fallbacks when provider credentials are missing, preserving lifecycle flow in local/dev runs.
- Added caller/session metadata extraction helpers to resolve a normalized caller ID from available context payloads/participant metadata for the lifecycle fallback path.
- Composed `CallLifecycle` around the real `AgentSession`, attached lifecycle event subscriptions before session start, and preserved `build_runtime_agent()` as the runtime construction seam.
- Ensured the same runtime controller instance is used by both lifecycle and `session.start(...)` while still preserving the `build_runtime_agent(...)` call seam expected by entrypoint tests.
- Triggered `await session.generate_reply()` after `await session.start(...)` to close the initial inbound silence gap.
- Added integration-client cleanup handlers on terminal session events (`close`, `away`, `end`).

Project bookkeeping updates:

- Marked T04 complete in `.gsd/milestones/M001/slices/S05/S05-PLAN.md`.
- Appended D036 to `.gsd/DECISIONS.md`.

## Verification

Ran the required slice verification commands:

- `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py` ✅ PASS (78 passed)
- `uv run ruff check src/ tests/` ✅ PASS

Also ran targeted entrypoint proof during implementation:

- `uv run pytest tests/test_agent.py` ✅ PASS (4 passed)

## Diagnostics

How to inspect this wiring later:

- Entrypoint composition regressions: `uv run pytest tests/test_agent.py`
- Full slice gate: `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`
- Lint/style gate: `uv run ruff check src/ tests/`
- Runtime observability:
  - `gate_checked` structured lifecycle event emitted from `src/agent.py`
  - `CallLifecycle` structured phases (`transcript_item_added`, `finalize_started`, `crm_result`, `sms_result`, `finalize_completed`)
  - `CallLifecycle.snapshot()` for finalized status/provider outcomes with redacted diagnostics

## Deviations

- None.

## Known Issues

- None.

## Files Created/Modified

- `src/agent.py` — wired S05 runtime entrypoint with dotenv loading, after-hours gate decision logging, lifecycle attachment, provider composition/fallback, caller-id extraction, and startup greeting trigger
- `.gsd/milestones/M001/slices/S05/S05-PLAN.md` — marked T04 as complete (`[x]`)
- `.gsd/DECISIONS.md` — appended D036 documenting entrypoint integration-provider fallback strategy
- `.gsd/milestones/M001/slices/S05/tasks/T04-SUMMARY.md` — recorded task completion summary and verification evidence
