---
id: T02
parent: S06
milestone: M001
provides:
  - Operator/bootstrap readiness artifacts (`README.md`, `.env.example`, `pyproject.toml`) required by S06 and CI-equivalent local setup.
key_files:
  - README.md
  - .env.example
  - pyproject.toml
  - uv.lock
  - .gsd/milestones/M001/slices/S06/S06-PLAN.md
key_decisions:
  - D040: Root manifest baseline uses setuptools `src/` discovery + explicit runtime deps + uv `dependency-groups.dev` for deterministic `uv sync --dev` bootstrap.
patterns_established:
  - Readiness artifacts are enforced by `tests/test_s06_readiness.py` and validated with `uv sync --dev` so documentation/config/bootstrap drift fails early.
observability_surfaces:
  - README now documents lifecycle diagnostics via `agent.lifecycle` structured phases and `CallLifecycle.snapshot()` inspection path.
duration: 1h05m
verification_result: passed
completed_at: 2026-03-11
# Set blocker_discovered: true only if execution revealed the remaining slice plan
# is fundamentally invalid (wrong API, missing capability, architectural mismatch).
# Do NOT set true for ordinary bugs, minor deviations, or fixable issues.
blocker_discovered: false
---

# T02: Implement README, env example, and pyproject bootstrap artifacts

**Shipped all three S06 bootstrap artifacts: actionable README runbook, placeholder-safe provider env template, and root pyproject manifest that makes `uv sync --dev` succeed in a clean clone.**

## What Happened

Implemented the T02 readiness package end-to-end:

- Added `README.md` with first-time setup steps, required environment variables, console/dev runtime commands (`src/agent.py`), verification commands, demo checklist (normal intake, safety escalation, partial hang-up), expected CRM/SMS outcomes, and lifecycle diagnostics guidance.
- Added `.env.example` with all required LiveKit, GoHighLevel, and Twilio key names using placeholder-only sample values (no secrets).
- Added `pyproject.toml` with:
  - `[project]` metadata and Python constraint (`>=3.12`),
  - runtime dependencies required by `src/` imports,
  - dev dependency group for pytest + Ruff,
  - pytest tool settings and baseline Ruff config,
  - setuptools `src/` package discovery to keep test/import behavior reproducible.
- Ran readiness tests and `uv sync --dev`, then adjusted pyproject Ruff configuration to avoid introducing non-slice lint policy changes (kept bootstrap-compatible config only).
- Marked T02 complete in `S06-PLAN.md`.

## Verification

Task-level verification (required by T02 plan):

- `uv run pytest tests/test_s06_readiness.py -q` ✅ (10 passed)
- `uv sync --dev` ✅ (resolved/audited cleanly)

Slice-level verification status captured per instructions:

- `uv run pytest tests/test_s06_readiness.py tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider` ✅ (11 passed)
- `uv sync --dev` ✅
- `uv run pytest` ✅ (131 passed)
- `uv run ruff check src/` ✅
- `uv run ruff format --check src/` ❌ expected remaining S06 work (9 files would be reformatted; owned by T03/T04)

## Diagnostics

Future inspection path added by this task:

- Read `README.md` for runbook/demo troubleshooting steps and expected post-call behavior.
- Use documented lifecycle phases in structured logs (`finalize_started`, `crm_result`, `sms_result`, `finalize_completed`) for runtime troubleshooting.
- Use `CallLifecycle.snapshot()` (documented in README with targeted test command) to inspect isolated CRM/SMS outcomes and failure metadata.

## Deviations

- `uv sync --dev` generated `uv.lock`; kept it as reproducibility evidence for clean-environment bootstrap.

## Known Issues

- Source formatting gate is still pending slice tasks T03/T04: `uv run ruff format --check src/` reports 9 files requiring formatting.

## Files Created/Modified

- `README.md` — Added operator-facing setup/run/verify/demo runbook with lifecycle diagnostics guidance.
- `.env.example` — Added required provider env keys with placeholder-only values.
- `pyproject.toml` — Added project metadata, runtime/dev dependencies, pytest config, Ruff config, and setuptools `src/` discovery.
- `uv.lock` — Added lockfile produced by `uv sync --dev` for deterministic dependency resolution.
- `.gsd/DECISIONS.md` — Appended D040 bootstrap manifest strategy decision.
- `.gsd/milestones/M001/slices/S06/S06-PLAN.md` — Marked T02 as complete (`[x]`).
