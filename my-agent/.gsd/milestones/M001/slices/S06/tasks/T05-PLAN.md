---
estimated_steps: 5
estimated_files: 2
---

# T05: Execute full S06 gate and update R010 traceability evidence

**Slice:** S06 — Full Test Suite and Demo Readiness
**Milestone:** M001

## Description

Run the final readiness gate end-to-end and document objective closure evidence so S06 can be marked complete with truthful requirement traceability.

## Steps

1. Run `uv sync --dev` in the refreshed project to validate clean-environment bootstrap.
2. Run the full test suite (`uv run pytest`) and confirm all behavior paths stay green.
3. Run source-quality gates (`uv run ruff check src/` and `uv run ruff format --check src/`).
4. Update `.gsd/REQUIREMENTS.md` so R010 has explicit validation mapping to the concrete S06 verification commands.
5. Write `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md` with executed commands/results, requirement impacts, and remaining live UAT follow-up notes.

## Must-Haves

- [ ] Full S06 command gate passes in a fresh run without skipping any required command.
- [ ] R010 is no longer unmapped and references repeatable verification evidence.
- [ ] S06 summary captures real command outputs/results and clearly states any remaining non-CI human/UAT proof.

## Verification

- `uv sync --dev && uv run pytest && uv run ruff check src/ && uv run ruff format --check src/`
- Manual check: `.gsd/REQUIREMENTS.md` traceability table includes concrete R010 proof mapping.

## Observability Impact

- Signals added/changed: Formalized closure evidence points future agents to exact commands/tests for readiness diagnosis.
- How a future agent inspects this: Use `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md` plus traceability entries in `.gsd/REQUIREMENTS.md`.
- Failure state exposed: Gate regressions are anchored to specific command outputs instead of informal completion claims.

## Inputs

- T01–T04 outputs (readiness tests, artifacts, and format-stabilized source tree).
- `.gsd/REQUIREMENTS.md` existing active requirement matrix.
- S05 summary/diagnostic conventions for evidence reporting continuity.

## Expected Output

- `.gsd/REQUIREMENTS.md` — updated R010 validation mapping and traceability consistency.
- `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md` — final S06 execution evidence and closure narrative.
