---
id: S05
parent: M001
milestone: M001
provides:
  - End-to-end after-hours runtime orchestration (gate + finalize-once lifecycle + CRM/SMS isolation + wired entrypoint greeting flow)
requires:
  - slice: S02
    provides: IntakeTask/slot diagnostics and live classification surfaces consumed by lifecycle finalization
  - slice: S03
    provides: HVAC conversation controller + safety/intake runtime behavior consumed by entrypoint/lifecycle wiring
  - slice: S04
    provides: CRM/SMS protocol boundaries and provider implementations consumed by call lifecycle execution
affects:
  - S06
key_files:
  - src/agent.py
  - src/orchestration/after_hours_gate.py
  - src/orchestration/call_lifecycle.py
  - src/orchestration/transcript_assembler.py
  - src/classification/final_classifier.py
  - src/orchestration/summary_builder.py
  - src/utils/time.py
  - src/utils/logging.py
  - src/hvac_types/business_config.py
  - src/hvac_types/call_intake_record.py
  - src/config/hvac_demo_config.py
  - src/config/load_config.py
  - tests/test_after_hours_gate.py
  - tests/test_call_lifecycle.py
  - tests/test_agent.py
  - tests/test_types.py
  - .gsd/REQUIREMENTS.md
key_decisions:
  - D034: Keep zoneinfo primary; allow deterministic Toronto fallback for injected-time gate checks when tzdata is unavailable.
  - D035: Finalization source-of-truth is committed transcript events + controller diagnostics with redacted observability surfaces.
  - D036: Entrypoint composes real providers when configured and protocol-compatible no-op fallbacks when credentials are absent.
patterns_established:
  - Pure gate API (`is_after_hours(config, now=...)`) + typed decision surface.
  - Finalize-once lifecycle orchestration with independent CRM/SMS execution and redacted provider diagnostics.
  - Entrypoint composes one runtime controller instance, attaches lifecycle before session start, then triggers initial `generate_reply()`.
observability_surfaces:
  - `CallLifecycle.snapshot()`
  - structured lifecycle log events (`gate_checked`, `transcript_item_added`, `finalize_started`, `crm_result`, `sms_result`, `finalize_completed`)
  - `IntegrationError.to_dict()`-style redacted provider diagnostics
  - pytest seams: `tests/test_after_hours_gate.py`, `tests/test_call_lifecycle.py`, `tests/test_agent.py`
drill_down_paths:
  - .gsd/milestones/M001/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S05/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S05/tasks/T03-SUMMARY.md
  - .gsd/milestones/M001/slices/S05/tasks/T04-SUMMARY.md
duration: 4h25m
verification_result: passed
completed_at: 2026-03-11
---

# S05: Call Lifecycle Orchestration and After-Hours Gate

**Shipped the real S05 runtime boundary: timezone-safe after-hours gating, finalize-once call lifecycle orchestration, and a fully wired `src/agent.py` entrypoint that persists complete/partial calls and isolates CRM/SMS failures.**

## What Happened

S05 closed in four steps:

1. **T01 (RED boundary):** Added strict S05 tests for gate math, lifecycle finalize behavior, entrypoint wiring, and expanded shared contracts.
2. **T02 (contracts + gate):** Extended `BusinessConfig` and `CallIntakeRecord` for after-hours and caller-ID fallback semantics, added strict config validation, and implemented pure timezone-safe gate/time helpers.
3. **T03 (orchestration core):** Implemented transcript assembly, deterministic final classification + summary derivation, and `CallLifecycle` finalize-once orchestration with independent CRM/SMS outcomes and stable diagnostics.
4. **T04 (entrypoint wiring):** Wired `src/agent.py` with explicit dotenv loading, gate evaluation/logging, lifecycle composition around `AgentSession`, startup greeting trigger, and provider composition/fallback behavior.

Also updated requirement traceability for newly proven S05 requirements.

## Verification

Executed fresh slice-level verification from the S05 plan:

- `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py` ✅ (78 passed)
- `uv run ruff check src/ tests/` ✅ (all checks passed)

## Requirements Advanced

- **R005** — S05 now proves runtime orchestration actually drives CRM writes from finalized lifecycle records without coupling CRM success to SMS success.
- **R008** — after-hours operating window is now fully config-driven (`BusinessConfig` + loader validation + demo defaults).

## Requirements Validated

- **R007** — validated by `tests/test_after_hours_gate.py`, `tests/test_agent.py`, `tests/test_types.py` (timezone-aware overnight gate, config validation, and entrypoint wiring).
- **R009** — validated by `tests/test_call_lifecycle.py` and `tests/test_agent.py` (partial-call finalize path, caller-ID fallback when callback unconfirmed, finalize-once idempotence, CRM/SMS isolation).

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- No material plan deviations. Implementation stayed within S05 task boundaries.

## Known Limitations

- Live credential/UAT proof for real GoHighLevel and Twilio delivery is still pending milestone follow-up (S06/demo closure).
- Full-milestone quality gates (`uv run pytest` entire suite, ruff format check, README/demo updates) remain S06 scope.

## Follow-ups

- Execute S06 full-suite/demo readiness gate, including live provider verification with credentials and final documentation closure.

## Files Created/Modified

- `src/orchestration/after_hours_gate.py` — pure gate decision surface with same-day/overnight timezone-aware logic.
- `src/utils/time.py` — strict time-window parsing and timezone resolution helpers with typed error surface.
- `src/orchestration/call_lifecycle.py` — finalize-once orchestration, provider isolation, and snapshot diagnostics.
- `src/orchestration/transcript_assembler.py` — committed conversation transcript assembly with noise filtering.
- `src/classification/final_classifier.py` — deterministic final classification contract.
- `src/orchestration/summary_builder.py` — deterministic summary builders for finalized records.
- `src/utils/logging.py` — structured lifecycle logging + redaction helpers.
- `src/agent.py` — wired runtime entrypoint (dotenv + gate + lifecycle + greeting + provider composition).
- `src/hvac_types/business_config.py` — after-hours config fields.
- `src/hvac_types/call_intake_record.py` — caller-ID fallback and callback-confirmation fields.
- `src/config/hvac_demo_config.py` — default after-hours window (`17:00` → `09:00`).
- `src/config/load_config.py` — strict validation for after-hours window presence/format.
- `tests/test_after_hours_gate.py` — gate boundary and timezone behavior coverage.
- `tests/test_call_lifecycle.py` — finalize semantics, isolation, and diagnostics coverage.
- `tests/test_agent.py` — entrypoint wiring assertions.
- `tests/test_types.py` — expanded type/config contract tests.
- `.gsd/REQUIREMENTS.md` — added S05 validation evidence for R007/R009 and refreshed summary counts.

## Forward Intelligence

### What the next slice should know
- `CallLifecycle.snapshot()` is the fastest trustworthy status surface for post-call behavior (finalized state, provider outcomes, fallback usage).

### What's fragile
- Timezone behavior in environments lacking tzdata is intentionally constrained to deterministic injected-time fallback; runtime zone resolution still requires valid tz data.

### Authoritative diagnostics
- Start with `tests/test_call_lifecycle.py` + `CallLifecycle.snapshot()` for lifecycle regressions; use `tests/test_agent.py` for entrypoint wiring regressions.

### What assumptions changed
- Assumption: provider clients should always be hard-required at startup.
- Actual: runtime now composes no-op protocol-compatible provider fallbacks when credentials are absent (D036), preserving local/dev operability while keeping real provider paths available.
