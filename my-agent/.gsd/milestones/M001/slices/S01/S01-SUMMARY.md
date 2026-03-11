---
id: S01
parent: M001
milestone: M001
provides:
  - Core typed contracts (`BusinessConfig`, `CallIntakeRecord`, `CallStatus`, classification enums, slot state types)
  - Default HVAC demo config profile (`HVAC_DEMO_CONFIG`)
  - Runtime config loader with fail-fast required-field validation (`load_config`)
requires: []
affects:
  - M001/S02
  - M001/S04
  - M001/S05
key_files:
  - src/hvac_types/__init__.py
  - src/hvac_types/classification.py
  - src/hvac_types/slot_state.py
  - src/hvac_types/business_config.py
  - src/hvac_types/call_intake_record.py
  - src/config/hvac_demo_config.py
  - src/config/load_config.py
  - tests/test_types.py
key_decisions:
  - All project `str, Enum` types override `__str__` to return `self.value` for Python 3.13 compatibility.
  - Runtime config is validated eagerly at load time for required non-empty string fields.
patterns_established:
  - Dataclass mutable fields always use `field(default_factory=...)`.
  - Boot-time config validation must be whitespace-aware and field-specific in error messages.
observability_surfaces:
  - `load_config()` raises actionable `ValueError` naming the missing/invalid required field.
drill_down_paths:
  - .gsd/milestones/M001/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T03-SUMMARY.md
duration: ~96m total across T01-T03
verification_result: passed
completed_at: 2026-03-11
---

# S01: Core Types, Config, and Data Model

**Shipped the full typed data/config contract for the HVAC agent, plus validated demo config loading with fail-fast boot errors.**

## What Happened

S01 delivered the foundational contracts consumed by all later slices:

- Created `src/hvac_types/` package and public API exports.
- Implemented classification enums (`IssueCategory`, `UrgencyLevel`, `DangerType`) and slot state types (`SlotStatus`, `SlotState`).
- Implemented `BusinessConfig` and `CallIntakeRecord` (+ `CallStatus`) dataclasses for runtime config and persisted intake output.
- Added default demo profile in `src/config/hvac_demo_config.py` as `HVAC_DEMO_CONFIG`.
- Added `load_config(config=None)` in `src/config/load_config.py` with required-field validation for `business_name`, `timezone`, and `owner_phone`.

Cross-task quality hardening also landed:

- Added `__str__` overrides on all `str, Enum` classes to preserve value-string behavior on Python 3.13.
- Ensured all mutable dataclass fields use `default_factory` to avoid shared instance state.
- Validation is whitespace-aware and reports the exact failing field.

Test coverage in `tests/test_types.py` now covers enum values/behavior, dataclass defaults, mutable default isolation, and config loader success/failure behavior.

## Verification

Ran slice-level verification commands from the S01 plan:

- `uv run pytest tests/test_types.py` → **50 passed**
- `uv run ruff check src/ tests/` → **All checks passed**

Additional observability check:

- `uv run python -c "... load_config(BusinessConfig()) ..."` confirmed `ValueError` is raised with actionable field-specific message.

## Requirements Advanced

- R008 — Added typed `BusinessConfig`, default demo profile, and boot-time required-field validation so config-driven behavior is enforceable before runtime.
- R001 — Established required data record shape (`CallIntakeRecord`) used by later intake lifecycle slices.
- R003 — Established danger classification vocabulary (`DangerType`) needed for safety-branch behavior.
- R004 — Established issue/urgency classification enums consumed by live/final classifiers in later slices.
- R005 — Established CRM-target call record contract for downstream mapper/service work.
- R006 — Established owner contact configuration field (`owner_phone`) needed by alerting logic.

## Requirements Validated

- none fully validated in this slice (this slice provides contract-level proof, not end-to-end runtime behavior).

## New Requirements Surfaced

- none.

## Requirements Invalidated or Re-scoped

- none.

## Deviations

- None from planned scope.

## Known Limitations

- No slot-filling runtime logic yet (S02).
- No conversation/safety handoff execution yet (S03).
- No CRM/SMS integrations yet (S04).
- No lifecycle orchestration/after-hours gate wiring yet (S05).

## Follow-ups

- Use these contracts directly in S02 slot tracker and classifier outputs to avoid duplicate type definitions.
- Keep all future `str, Enum` additions aligned with the `__str__` compatibility pattern.
- Reuse `load_config()` as the single runtime entrypoint to prevent bypassing validation.

## Files Created/Modified

- `src/hvac_types/__init__.py` — Package exports for shared type imports.
- `src/hvac_types/classification.py` — Issue/urgency/danger enum vocabulary.
- `src/hvac_types/slot_state.py` — Slot status enum + mutable slot state dataclass.
- `src/hvac_types/business_config.py` — Typed business configuration model.
- `src/hvac_types/call_intake_record.py` — Final call record contract + call status enum.
- `src/config/__init__.py` — Config package public exports.
- `src/config/hvac_demo_config.py` — Default HVAC demo profile.
- `src/config/load_config.py` — Runtime config loader + required-field validation.
- `tests/test_types.py` — Contract-level test suite (50 tests).

## Forward Intelligence

### What the next slice should know
- Types are stable and importable; build S02 APIs against `hvac_types` directly instead of introducing parallel schema modules.
- `load_config()` is already the enforced validation boundary for required business identity/contact fields.

### What's fragile
- Enum string behavior across Python versions is fragile without the explicit `__str__` override.
- Any bypass of `load_config()` can silently admit invalid runtime config.

### Authoritative diagnostics
- `tests/test_types.py` is the canonical contract test surface for this slice.
- `load_config()` ValueError messages are the authoritative boot-time misconfiguration signal.

### What assumptions changed
- Assumption: `str, Enum` string conversion would always return raw values.
- Actual: Python 3.13 behavior required explicit `__str__` overrides to preserve expected value semantics.
