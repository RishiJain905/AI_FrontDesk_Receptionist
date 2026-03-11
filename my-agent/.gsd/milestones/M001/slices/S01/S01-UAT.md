# S01: Core Types, Config, and Data Model — UAT

**Milestone:** M001
**Written:** 2026-03-11

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S01 is a pure contract/config slice with no live call runtime path; correctness is proven by type-level tests and validation behavior checks.

## Preconditions

- Python environment resolves project dependencies via `uv`.
- Repository includes `src/hvac_types/`, `src/config/`, and `tests/test_types.py`.

## Smoke Test

Run `uv run pytest tests/test_types.py` and confirm all tests pass.

## Test Cases

### 1. Required config validation fails fast

1. Create `BusinessConfig()` with missing required field(s).
2. Call `load_config(cfg)`.
3. **Expected:** `ValueError` is raised and includes the invalid field name (`business_name`, `timezone`, or `owner_phone`).

### 2. Demo profile validates successfully

1. Import `HVAC_DEMO_CONFIG`.
2. Call `load_config(HVAC_DEMO_CONFIG)`.
3. **Expected:** Function returns the same config object and raises no error.

### 3. Dataclass mutable defaults are isolated

1. Instantiate two `BusinessConfig()` objects.
2. Append values to list fields on the first instance.
3. **Expected:** Second instance list fields remain empty (no shared mutable defaults).

## Edge Cases

### Whitespace-only required fields

1. Set one required config field to `"   "`.
2. Call `load_config(cfg)`.
3. **Expected:** Validation fails with `ValueError` for that field.

## Failure Signals

- `pytest` reports failing tests in `tests/test_types.py`.
- `load_config()` accepts missing/blank required fields.
- Enum `str()` values return member reprs instead of raw tokens.
- Mutable list defaults leak across dataclass instances.

## Requirements Proved By This UAT

- R008 (partial) — Proves typed config contract exists and required fields are validated at load-time.

## Not Proven By This UAT

- Full R008 scope (environment override layer and runtime use across all core logic).
- R001/R002/R003/R004 runtime conversational behavior.
- R005/R006 integration behavior.
- R007 after-hours gating.
- R009 failure handling in live call lifecycle.
- R010 end-to-end major-path test coverage.

## Notes for Tester

- This UAT is intentionally code-contract focused; no LiveKit console call flow is expected in S01.
- Use `tests/test_types.py` as the authoritative proof artifact for this slice.
