# S06: Full Test Suite and Demo Readiness

**Goal:** Close M001 by hardening release readiness: lock demo/bootstrap artifacts behind tests, restore reproducible `uv sync --dev` project metadata, pass full pytest + Ruff gates, and document how to run and demo the HVAC after-hours agent.
**Demo:** From a clean clone, an engineer can run `uv sync --dev`, execute the full test suite and Ruff gates successfully, follow `README.md` to run `src/agent.py` in console mode, and use the documented demo script to validate normal intake, safety escalation, and partial-call behavior while preserving lifecycle diagnostics.

## Must-Haves

- R010 is directly advanced with explicit S06 readiness tests plus fresh full-suite verification (`uv run pytest`) covering the roadmap behavior matrix (normal intake, partial call, safety branch, no-heat urgency, missing fields, outside-hours gate, CRM/SMS isolation).
- Demo/readiness artifacts exist and are enforced by tests: `README.md` (setup/run/verify/demo instructions), `.env.example` (required keys only), and root `pyproject.toml` compatible with CI `uv sync --dev` workflows.
- Source formatting/lint gates pass exactly as required by milestone DoD: `uv run ruff check src/` and `uv run ruff format --check src/`.
- Observability/failure diagnostics remain inspectable and verified via lifecycle failure-path assertions (`CallLifecycle.snapshot()` + redacted provider error metadata), so regressions are localizable.
- Requirement traceability is updated so R010 is no longer unmapped and points to concrete, repeatable verification commands.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: no
- Human/UAT required: yes

## Verification

- `uv run pytest tests/test_s06_readiness.py tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider`
- `uv sync --dev`
- `uv run pytest`
- `uv run ruff check src/`
- `uv run ruff format --check src/`

## Observability / Diagnostics

- Runtime signals: existing structured lifecycle events (`finalize_started`, `crm_result`, `sms_result`, `finalize_completed`) remain the authoritative post-call diagnostics.
- Inspection surfaces: `CallLifecycle.snapshot()` and targeted lifecycle failure-path tests in `tests/test_call_lifecycle.py`.
- Failure visibility: provider failures remain explicit (`service`, `operation`, `status_code`) with isolated CRM/SMS outcomes so one integration failure does not mask the other.
- Redaction constraints: no secret/token values in logs, snapshots, README examples, or `.env.example`; diagnostics must stay redacted by design.

## Integration Closure

- Upstream surfaces consumed: `src/agent.py`, `src/orchestration/call_lifecycle.py`, `src/utils/logging.py`, full pytest suites under `tests/`, and CI workflows under `.github/workflows/`.
- New wiring introduced in this slice: repository-level readiness wiring (`README.md` demo/runbook contract, `.env.example` config contract, `pyproject.toml` bootstrap contract, and S06 readiness tests enforcing them).
- What remains before the milestone is truly usable end-to-end: live GoHighLevel + Twilio credential-backed demo/UAT evidence (human-executed runtime proof outside deterministic CI/mock transport gates).

## Tasks

- [x] **T01: Add RED readiness tests for docs/bootstrap contracts** `est:45m`
  - Why: S06 needs objective, test-enforced proof for demo artifacts and bootstrap hygiene; without a RED boundary, docs/manifest work can regress silently.
  - Files: `tests/test_s06_readiness.py`
  - Do: Create a new pytest module that fails until `README.md`, `.env.example`, and `pyproject.toml` exist with required sections/keys/metadata; assert README includes setup/run/verify/demo commands and `.env.example` lists required LiveKit/GHL/Twilio keys without real values.
  - Verify: `uv run pytest tests/test_s06_readiness.py -q`
  - Done when: The new test file exists, collects cleanly, and initially fails only because readiness artifacts/fields are missing or incomplete.
- [x] **T02: Implement README, env example, and pyproject bootstrap artifacts** `est:1h15m`
  - Why: The current repo is missing core operator/bootstrap assets required by S06 and CI reproducibility.
  - Files: `README.md`, `.env.example`, `pyproject.toml`
  - Do: Author a milestone-accurate README (setup, env vars, console/dev run, verification commands, demo script, expected CRM/SMS outcomes), add `.env.example` with all required key names and safe placeholders, and add `pyproject.toml` with runtime + dev dependencies and tool config needed for `uv sync --dev`, pytest, and Ruff.
  - Verify: `uv run pytest tests/test_s06_readiness.py -q && uv sync --dev`
  - Done when: `tests/test_s06_readiness.py` passes and a clean `uv sync --dev` succeeds with the new manifest.
- [x] **T03: Apply Ruff formatting to agent/controller/classification surfaces** `est:45m`
  - Why: `ruff format --check src/` currently fails; these high-change runtime modules need normalized formatting before final gate closure.
  - Files: `src/agent.py`, `src/classification/rules.py`, `src/conversation/__init__.py`, `src/conversation/conversation_controller.py`, `src/conversation/intake_task.py`, `src/conversation/prompts.py`
  - Do: Run Ruff formatter on the listed modules, keep behavior unchanged, and resolve any style-induced import/order issues without prompt/logic churn.
  - Verify: `uv run pytest tests/test_conversation_controller.py tests/test_intake_task.py tests/test_agent.py -q && uv run ruff format --check src/agent.py src/classification/rules.py src/conversation/__init__.py src/conversation/conversation_controller.py src/conversation/intake_task.py src/conversation/prompts.py`
  - Done when: All listed files are Ruff-format clean and targeted controller/intake tests still pass.
- [x] **T04: Apply Ruff formatting to lifecycle utilities and re-verify diagnostics path** `est:45m`
  - Why: Remaining source files still block the formatter gate and must be validated alongside failure-path observability guarantees.
  - Files: `src/orchestration/after_hours_gate.py`, `src/orchestration/call_lifecycle.py`, `src/utils/__init__.py`, `tests/test_call_lifecycle.py`
  - Do: Format the remaining unformatted source files, keep lifecycle behavior intact, and run the provider-failure diagnostic test to ensure `snapshot()` error visibility/redaction still holds.
  - Verify: `uv run pytest tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider -q && uv run ruff check src/ && uv run ruff format --check src/`
  - Done when: Source-tree Ruff lint/format gates pass and the lifecycle diagnostic failure-path assertion remains green.
- [x] **T05: Execute full S06 gate and update R010 traceability evidence** `est:45m`
  - Why: S06 closes only with a fresh end-to-end quality pass and explicit requirement traceability updates.
  - Files: `.gsd/REQUIREMENTS.md`, `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md`
  - Do: Run the full milestone gate (`uv run pytest`, `ruff check`, `ruff format --check`), then update requirements traceability so R010 maps to concrete verification commands and record the final S06 execution evidence in the slice summary.
  - Verify: `uv run pytest && uv run ruff check src/ && uv run ruff format --check src/`
  - Done when: Full gates pass in a fresh run, R010 has explicit validation mapping, and S06 summary documents objective evidence for milestone closure.

## Files Likely Touched

- `tests/test_s06_readiness.py`
- `README.md`
- `.env.example`
- `pyproject.toml`
- `src/agent.py`
- `src/classification/rules.py`
- `src/conversation/__init__.py`
- `src/conversation/conversation_controller.py`
- `src/conversation/intake_task.py`
- `src/conversation/prompts.py`
- `src/orchestration/after_hours_gate.py`
- `src/orchestration/call_lifecycle.py`
- `src/utils/__init__.py`
- `tests/test_call_lifecycle.py`
- `.gsd/REQUIREMENTS.md`
- `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md`
