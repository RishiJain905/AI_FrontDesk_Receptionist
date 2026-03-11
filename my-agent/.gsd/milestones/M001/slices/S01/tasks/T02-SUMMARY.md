---
id: T02
parent: S01
milestone: M001
provides:
  - BusinessConfig and CallIntakeRecord typed data contracts with safe mutable defaults and finalized call status typing
key_files:
  - src/hvac_types/business_config.py
  - src/hvac_types/call_intake_record.py
  - tests/test_types.py
key_decisions:
  - Added __str__ override to CallStatus str enum to preserve value-string behavior across Python versions
patterns_established:
  - All mutable dataclass fields use field(default_factory=list) to avoid shared state between instances
observability_surfaces:
  - none
duration: 20m
verification_result: passed
completed_at: 2026-03-11
blocker_discovered: false
---

# T02: Data Models for Configuration and Final Intake

**Shipped BusinessConfig and CallIntakeRecord core types with tests proving list default isolation and None-based default intake state.**

## What Happened

Implemented `BusinessConfig` in `src/hvac_types/business_config.py` as a dataclass with optional scalar metadata and four mutable list fields (`safety_keywords`, `no_heat_keywords`, `no_cool_keywords`, `dispatcher_contacts`) all using `field(default_factory=list)`.

Implemented `CallStatus` and `CallIntakeRecord` in `src/hvac_types/call_intake_record.py`. `CallStatus` is a `str, Enum` with `partial` and `complete` values and a `__str__` override aligned with project enum behavior. `CallIntakeRecord` captures finalized intake output with optional fields for customer/contact/address data, issue classification (`IssueCategory`, `UrgencyLevel`, `DangerType`), booleans, and free-text summary/notes.

Extended `tests/test_types.py` with:
- `TestBusinessConfig` coverage for default values and cross-instance mutable list independence
- `TestCallStatus` enum behavior checks
- `TestCallIntakeRecord` assertion that default construction sets all fields to `None`

## Verification

- Ran: `uv run pytest tests/test_types.py` → **42 passed**
- Ran: `uv run ruff check src/ tests/` → **All checks passed**

Slice-level verification status after this task:
- `uv run pytest tests/test_types.py` ✅
- `uv run ruff check src/ tests/` ✅

## Diagnostics

None (pure type definitions; no runtime diagnostics surface in this task).

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/hvac_types/business_config.py` — Added BusinessConfig dataclass with safe list default factories.
- `src/hvac_types/call_intake_record.py` — Added CallStatus enum and CallIntakeRecord dataclass.
- `tests/test_types.py` — Added tests for BusinessConfig and CallIntakeRecord models plus CallStatus enum.
- `.gsd/milestones/M001/slices/S01/S01-PLAN.md` — Marked T02 complete (`[x]`).
