---
id: T01
parent: S06
milestone: M001
provides:
  - RED readiness-test boundary enforcing S06 demo/bootstrap artifact contracts before implementation
key_files:
  - tests/test_s06_readiness.py
  - .gsd/milestones/M001/slices/S06/S06-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/STATE.md
key_decisions:
  - Added D039: readiness tests must enforce README command evidence, provider env key coverage with placeholder-only values, and pyproject metadata/tool schema requirements
patterns_established:
  - Deterministic readiness assertions localize missing artifact/section failures to README, .env.example, or pyproject contracts
observability_surfaces:
  - uv run pytest tests/test_s06_readiness.py -q
  - assertion names/messages in tests/test_s06_readiness.py
  - slice verification command outcomes captured in this summary
duration: 45m
verification_result: passed
completed_at: 2026-03-11
blocker_discovered: false
---

# T01: Add RED readiness tests for docs/bootstrap contracts

**Added `tests/test_s06_readiness.py` as the S06 RED readiness contract so missing/incomplete README, `.env.example`, and `pyproject.toml` requirements now fail deterministically.**

## What Happened

Implemented `tests/test_s06_readiness.py` with explicit readiness assertions covering all T01 contract areas:

- Root readiness artifact existence checks for:
  - `README.md`
  - `.env.example`
  - `pyproject.toml`
- README contract checks for:
  - setup instructions
  - environment variable documentation
  - console/dev run guidance (`src/agent.py` + console/dev language)
  - command-level verification evidence (`uv run pytest`, `uv run ruff check src/`, `uv run ruff format --check src/`)
  - demo script coverage language for normal, safety, and partial call paths
- `.env.example` contract checks for required provider keys:
  - LiveKit: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
  - GoHighLevel: `GHL_API_TOKEN`, `GHL_LOCATION_ID`
  - Twilio: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
- `.env.example` placeholder guardrails requiring sample values to look like placeholders (and not empty/null-like values).
- `pyproject.toml` contract checks (via `tomllib`) for:
  - `[project]` metadata (`name`, `version`, `description`, `requires-python`)
  - Python constraint support for CI (`>=3.12`)
  - runtime dependencies including `livekit-agents`, `httpx`, and `python-dotenv`
  - pytest and Ruff config surfaces (`[tool.pytest.ini_options]`, `[tool.ruff]`)
  - dev dependencies including `pytest` and `ruff`.

Bookkeeping updates completed for this task:

- Marked T01 as done in `.gsd/milestones/M001/slices/S06/S06-PLAN.md`.
- Updated `.gsd/STATE.md` to move active work to T02.
- Appended D039 to `.gsd/DECISIONS.md` documenting readiness-contract strictness.

## Verification

Task-level verification:

- `uv run pytest tests/test_s06_readiness.py -q` ✅ Expected RED behavior (10 failures), with failures attributable to missing readiness artifacts (`README.md`, `.env.example`, `pyproject.toml`).

Slice-level verification commands (run per S06 plan; partial success expected at T01):

- `uv run pytest tests/test_s06_readiness.py tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider` ⚠️ PARTIAL
  - readiness tests failed as expected (missing artifacts)
  - lifecycle diagnostic test passed
- `uv sync --dev` ❌ FAIL (expected at this stage): no `pyproject.toml`
- `uv run pytest` ❌ FAIL
  - expected new readiness RED failures
  - existing unrelated failures also present in `tests/test_conversation_controller.py` (2 intent-judge failures)
- `uv run ruff check src/` ✅ PASS
- `uv run ruff format --check src/` ❌ FAIL (9 source files reported as needing reformat; slated for T03/T04)

## Diagnostics

How to inspect this task’s readiness boundary:

- Run `uv run pytest tests/test_s06_readiness.py -q`.
- Read assertion names/messages in `tests/test_s06_readiness.py` to localize missing contracts by artifact type.
- Use the slice verification sequence in `S06-PLAN.md` to confirm partial-vs-full closure status as later tasks complete.

## Deviations

- None.

## Known Issues

- `tests/test_conversation_controller.py` currently has 2 unrelated LLM-judging failures in full-suite runs; not in T01 scope.
- `uv sync --dev` remains blocked until T02 adds `pyproject.toml`.

## Files Created/Modified

- `tests/test_s06_readiness.py` — new RED readiness contract tests for README/env/manifest expectations
- `.gsd/milestones/M001/slices/S06/S06-PLAN.md` — marked T01 complete (`[x]`)
- `.gsd/DECISIONS.md` — appended D039 (readiness contract strictness)
- `.gsd/STATE.md` — advanced active task/next action to T02
- `.gsd/milestones/M001/slices/S06/tasks/T01-SUMMARY.md` — recorded T01 implementation and verification evidence
