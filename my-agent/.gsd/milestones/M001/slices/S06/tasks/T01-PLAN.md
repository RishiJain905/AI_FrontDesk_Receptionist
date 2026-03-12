---
estimated_steps: 4
estimated_files: 1
---

# T01: Add RED readiness tests for docs/bootstrap contracts

**Slice:** S06 — Full Test Suite and Demo Readiness
**Milestone:** M001

## Description

Create the S06 RED boundary by adding readiness tests that enforce required demo/boot artifacts before implementation work begins. The tests should fail initially against the current repo state and become the contract for README/env/manifest completion.

## Steps

1. Create `tests/test_s06_readiness.py` with assertions that `README.md`, `.env.example`, and `pyproject.toml` exist at repo root.
2. Add README assertions for required sections/commands: setup, environment variables, console/dev run, verification (`uv run pytest`, Ruff checks), and a demo script covering normal/safety/partial paths.
3. Add `.env.example` assertions for required key names (LiveKit, GoHighLevel, Twilio) and guardrails that sample values are placeholders, not real secrets.
4. Add `pyproject.toml` assertions using `tomllib` to require `[project]` metadata, Python version constraint, runtime dependencies, and pytest/Ruff tool configuration, then run the targeted pytest command to confirm RED failure.

## Must-Haves

- [ ] Tests fail when any required readiness artifact is missing or missing mandatory content.
- [ ] Tests enforce command-level evidence expectations (full pytest + Ruff lint/format checks present in docs).
- [ ] Tests never require real credentials; they only validate key names/placeholder safety.

## Verification

- `uv run pytest tests/test_s06_readiness.py -q`
- Expected initial result: FAIL, with failures attributable only to missing/incomplete readiness artifacts.

## Observability Impact

- Signals added/changed: A deterministic readiness test contract that reports exactly which artifact/section is missing.
- How a future agent inspects this: Run `uv run pytest tests/test_s06_readiness.py -q` and inspect assertion names for missing artifact localization.
- Failure state exposed: Missing README sections, missing env keys, or incomplete `pyproject.toml` schema become explicit failing assertions.

## Inputs

- `.gsd/milestones/M001/slices/S06/S06-PLAN.md` — defines S06 verification and artifact requirements.
- `.github/workflows/tests.yml` and `.github/workflows/ruff.yml` — define CI expectations (`uv sync --dev`, pytest, Ruff gates).

## Expected Output

- `tests/test_s06_readiness.py` — failing-but-collecting RED tests codifying S06 demo/bootstrap contracts.
