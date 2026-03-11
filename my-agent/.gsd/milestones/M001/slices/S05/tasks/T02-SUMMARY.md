---
id: T02
parent: S05
milestone: M001
provides:
  - Config/record contract expansion plus a pure, timezone-safe after-hours gate boundary with deterministic test-time clock injection.
key_files:
  - src/hvac_types/business_config.py
  - src/hvac_types/call_intake_record.py
  - src/config/hvac_demo_config.py
  - src/config/load_config.py
  - src/utils/time.py
  - src/orchestration/after_hours_gate.py
  - tests/test_types.py
  - .gsd/milestones/M001/slices/S05/S05-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/STATE.md
key_decisions:
  - D034: Keep `zoneinfo` as the primary resolver, but allow deterministic Toronto fallback for injected-time gate evaluation when tzdata is unavailable on Windows-like environments.
patterns_established:
  - Gate logic is now a pure function (`is_after_hours(config, now=...)`) returning a typed `GateDecision` with deterministic inputs/outputs.
observability_surfaces:
  - `orchestration.after_hours_gate.GateDecision`
  - `utils.time.TimezoneResolutionError`
  - `tests/test_after_hours_gate.py` and `tests/test_types.py`
duration: 1h10m
verification_result: passed
completed_at: 2026-03-11 19:20 EDT
blocker_discovered: false
---

# T02: Extend the config and record contracts and implement the timezone-safe after-hours gate

**Extended the shared S05 contracts and shipped a pure, injectable after-hours gate with strict config/time validation at the boundary.**

## What Happened

Implemented all T02 plan steps across config/types/time/gate surfaces:

- Extended `BusinessConfig` with explicit after-hours window fields:
  - `after_hours_start: str | None`
  - `after_hours_end: str | None`
- Extended `CallIntakeRecord` with explicit fallback-phone lifecycle fields:
  - `callback_number_confirmed: bool | None`
  - `caller_id: str | None`
- Updated demo config defaults in `src/config/hvac_demo_config.py`:
  - `after_hours_start="17:00"`
  - `after_hours_end="09:00"`
- Strengthened config validation in `src/config/load_config.py`:
  - retains required identity fields (`business_name`, `timezone`, `owner_phone`)
  - now rejects missing/blank after-hours fields
  - now rejects unparseable after-hours values by enforcing strict `HH:MM` parsing before runtime boot
- Added `src/utils/time.py` with shared helpers:
  - `TimezoneResolutionError`
  - `resolve_timezone(...)` with clear, actionable tzdata error messaging for Windows-like environments
  - strict time parsing (`parse_time_of_day`, `parse_time_window`)
  - injectable local clock helper (`get_local_now(..., now=...)`)
- Added `src/orchestration/after_hours_gate.py` with pure gate logic:
  - `GateDecision` typed output (decision + timezone/window metadata)
  - `is_after_hours(config, now=...)` supporting deterministic injected datetimes
  - correct same-day and overnight window behavior
  - bypasses runtime clock lookup when `now` is injected
  - preserves typed timezone failures for unresolved zones
- Added targeted RED→GREEN test coverage for stricter after-hours config validation in `tests/test_types.py`:
  - missing window fields fail validation
  - blank window fields fail validation
  - unparseable window values fail validation

## Verification

Task-level verification (required by T02 plan):

- `uv run pytest tests/test_after_hours_gate.py tests/test_types.py`
  - **PASS** (69 passed)

Slice-level verification checks (run per S05 plan requirement, intermediate-task partial expected):

- `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`
  - **PARTIAL / EXPECTED FAIL** at collection: `ModuleNotFoundError: classification.final_classifier` (T03 scope)
- `uv run ruff check src/ tests/`
  - **PASS** (`All checks passed!`)

## Diagnostics

How to inspect this boundary later:

- Gate math and injectable clock behavior:
  - `uv run pytest tests/test_after_hours_gate.py`
- Contract + config validation boundary:
  - `uv run pytest tests/test_types.py -k "after_hours or callback_number_confirmed or caller_id"`
- Direct runtime-surface checks:
  - import `is_after_hours` and pass an explicit UTC `datetime` to inspect deterministic `GateDecision`
  - import `resolve_timezone` and verify typed failures (`TimezoneResolutionError`) for bad timezone inputs

## Deviations

- Added a deterministic Toronto fallback path for injected-time gate evaluation when tzdata is unavailable locally, while keeping `zoneinfo` as the primary resolver and preserving typed failures for unresolved runtime timezone resolution.

## Known Issues

- Slice-level pytest remains RED for unimplemented T03 modules (`classification.final_classifier`, lifecycle orchestration surfaces), which is expected at this stage.

## Files Created/Modified

- `src/hvac_types/business_config.py` — added `after_hours_start` / `after_hours_end` fields.
- `src/hvac_types/call_intake_record.py` — added `callback_number_confirmed` and `caller_id` fields.
- `src/config/hvac_demo_config.py` — added default overnight after-hours window (`17:00` → `09:00`).
- `src/config/load_config.py` — added strict after-hours presence/format validation via shared time parser.
- `src/utils/time.py` — new timezone resolution + strict window parsing + injectable local-time helpers.
- `src/utils/__init__.py` — exported shared time helpers and `TimezoneResolutionError`.
- `src/orchestration/after_hours_gate.py` — new pure gate decision boundary with same-day/overnight handling.
- `src/orchestration/__init__.py` — new package export surface for gate helpers.
- `tests/test_types.py` — expanded load-config tests for missing/blank/unparseable after-hours windows.
- `.gsd/milestones/M001/slices/S05/S05-PLAN.md` — marked T02 as complete (`[x]`).
- `.gsd/DECISIONS.md` — appended D034 for timezone fallback behavior.
- `.gsd/STATE.md` — updated phase and next action for T03.
