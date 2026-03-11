---
id: T03
parent: S01
milestone: M001
provides:
  - `src/config/` package with demo profile and runtime validator
  - `HVAC_DEMO_CONFIG` default `BusinessConfig` singleton for HVAC after-hours flows
  - `load_config()` fail-fast validation for required fields (`business_name`, `timezone`, `owner_phone`)
  - Expanded type/test coverage for required BusinessConfig identity/contact fields
key_files:
  - src/config/__init__.py
  - src/config/hvac_demo_config.py
  - src/config/load_config.py
  - src/hvac_types/business_config.py
  - tests/test_types.py
key_decisions:
  - Added eager, whitespace-aware required-field validation in `load_config()` to fail on boot rather than during downstream runtime operations
patterns_established:
  - Runtime config entrypoints must validate required string fields as non-empty (`value.strip()` truthy) before accepting config state
observability_surfaces:
  - `ValueError` raised at initialization with explicit missing field name when config is invalid
duration: 31m
verification_result: passed
completed_at: 2026-03-11
blocker_discovered: false
---

# T03: Demo Config Profile and Runtime Validator

**Added the default HVAC demo configuration and boot-time config validator, with tests proving invalid required fields fail fast and demo config loads successfully.**

## What Happened

Implemented the new `src/config/` package:

- `src/config/hvac_demo_config.py` defines `HVAC_DEMO_CONFIG` as a single static `BusinessConfig` instance populated for an HVAC after-hours profile (Toronto timezone, owner phone, safety/no-heat/no-cool keywords, dispatcher contacts).
- `src/config/load_config.py` adds `load_config(config: BusinessConfig | None = None) -> BusinessConfig`.
  - Falls back to `HVAC_DEMO_CONFIG` when no config is passed.
  - Validates required fields `business_name`, `timezone`, and `owner_phone` as non-empty strings (whitespace-only values are treated as invalid).
  - Raises `ValueError` with a descriptive message including the failing field name.
- `src/config/__init__.py` exports `HVAC_DEMO_CONFIG` and `load_config`.

Updated `BusinessConfig` in `src/hvac_types/business_config.py` to include:

- `owner_phone: str | None = None`
- `timezone: str | None = None`

Extended `tests/test_types.py` with `TestLoadConfig` coverage for:

- `None` required fields → `ValueError`
- Empty-string required fields → `ValueError`
- `load_config()` fallback returns `HVAC_DEMO_CONFIG`
- `HVAC_DEMO_CONFIG` passes validation

Also updated existing `TestBusinessConfig` defaults test to assert `owner_phone` and `timezone` default to `None`.

## Verification

- `uv run pytest tests/test_types.py` → **50 passed**
- `uv run ruff check src/ tests/` → **All checks passed**
- `uv run ruff format --check src/ tests/` → **12 files already formatted**

Slice-level verification status:

- `uv run pytest tests/test_types.py` ✅
- `uv run ruff check src/ tests/` ✅

## Diagnostics

Invalid runtime config now fails immediately during initialization via `load_config()` with a field-specific `ValueError`, making boot-time misconfiguration directly visible in stack traces.

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/config/__init__.py` — New config package exports for demo config and loader.
- `src/config/hvac_demo_config.py` — Added `HVAC_DEMO_CONFIG` singleton profile.
- `src/config/load_config.py` — Added boot-time validator and fallback loader.
- `src/hvac_types/business_config.py` — Added `owner_phone` and `timezone` fields.
- `tests/test_types.py` — Added load/validation tests and updated BusinessConfig default assertions.
- `.gsd/milestones/M001/slices/S01/S01-PLAN.md` — Marked T03 as complete.
- `.gsd/DECISIONS.md` — Appended D015 config boot-validation decision.
