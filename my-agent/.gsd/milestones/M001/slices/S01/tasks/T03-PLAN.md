---
estimated_steps: 4
estimated_files: 4
---

# T03: Demo Config Profile and Runtime Validator

**Slice:** S01 — Core Types, Config, and Data Model
**Milestone:** M001

## Description

Provides the default business configuration instance used by the LiveKit application and ensures that critical fields required by downstream services (e.g. `business_name`, `timezone`, `owner_phone`) are validated eagerly before accepting the config state.

## Steps

1. Create `src/config/` directory and `__init__.py`.
2. Write `src/config/hvac_demo_config.py` declaring `HVAC_DEMO_CONFIG: BusinessConfig`. Populate values that match an HVAC after-hours model (e.g., timezone `America/Toronto`, danger keywords, owner phone number).
3. Create `src/config/load_config.py` with `load_config(config: BusinessConfig | None = None) -> BusinessConfig`. If `config` is None, use `HVAC_DEMO_CONFIG`. Validate that the config object has required non-empty string fields (`business_name`, `timezone`, `owner_phone`). Raise a `ValueError` with a descriptive message if any are missing.
4. Update `tests/test_types.py` verifying that passing an empty string or None to required fields in a `BusinessConfig` raises `ValueError` when passed to `load_config()`, and that `HVAC_DEMO_CONFIG` passes successfully.

## Must-Haves

- [ ] `HVAC_DEMO_CONFIG` single static config instance holding default configuration profile.
- [ ] `load_config()` validator that fails fast on missing required fields and falls back to demo config if none is provided.
- [ ] Tests asserting that missing required fields throw a `ValueError` on boot before execution proceeds.

## Verification

- Run `uv run pytest tests/test_types.py`.
- Run `uv run ruff check src/ tests/` and `uv run ruff format --check src/ tests/` ensuring all code styles are cleanly met.

## Observability Impact

- Signals added/changed: Validation error thrown on missing config fields.
- How a future agent inspects this: A clear, descriptive stack trace and `ValueError` at runtime during initialization.
- Failure state exposed: Explicit validation errors on boot in `load_config()`.

## Inputs

- `src/hvac_types/business_config.py` — Needed to pass to `load_config()`.

## Expected Output

- `src/config/hvac_demo_config.py` — The demo config profile.
- `src/config/load_config.py` — The runtime validator.
- `tests/test_types.py` — Tests proving valid configs pass and invalid ones fail.
