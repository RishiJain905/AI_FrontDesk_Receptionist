---
estimated_steps: 4
estimated_files: 5
---

# T04: Run slice verification, tighten diagnostics, and document the planning handoff surfaces

**Slice:** S02 — Slot-Filling Intake and Background Classification
**Milestone:** M001

## Description

Close the slice honestly by running the full verification boundary, tightening any diagnostic surfaces that remain ambiguous, and leaving the S02 modules ready for S03/S05 to consume without hidden assumptions.

## Steps

1. Run the full S02 verification commands (`pytest` for both test files and `ruff check`) and capture any remaining failures tied to naming, diagnostics, or wiring.
2. Make small targeted refinements to tracker snapshots, classifier outputs, or intake-task state exposure so the failure modes described in the slice plan are directly inspectable by tests.
3. Re-run the full verification suite until all slice checks pass cleanly with no orphaned TODO behavior or hidden prompt-only dependencies.
4. Confirm the exported module surfaces and test assertions match the slice plan’s promised handoff contract for S03 (conversation controller/safety branch) and S05 (lifecycle classification consumers).

## Must-Haves

- [ ] The full slice verification command passes exactly as named in `S02-PLAN.md`.
- [ ] At least one test assertion exercises the diagnostic surfaces for missing/tentative slots or typed classification output, so observability promises are proven rather than merely described.

## Verification

- `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py && uv run ruff check src/ tests/`
- Confirm the passing suite covers both behavioral success paths and at least one inspectable failure-path/diagnostic signal.

## Observability Impact

- Signals added/changed: Finalizes and stabilizes the diagnostic surfaces exposed by slot snapshots, classifier outputs, and intake-task completion state.
- How a future agent inspects this: Use the named verification commands and the test assertions as the canonical localization path for S02 regressions.
- Failure state exposed: Any regression in adaptive slot semantics or classification logic will fail with a localized assertion against the typed inspection surfaces.

## Inputs

- `S02-PLAN.md` — Slice-level verification and observability commitments that this task must close honestly.
- `src/conversation/*.py`, `src/classification/*.py`, `tests/test_slot_filling.py`, `tests/test_intake_task.py` — Implemented slice artifacts from T02/T03.

## Expected Output

- `src/conversation/slot_tracker.py`, `src/classification/live_classifier.py`, `src/conversation/intake_task.py` — Finalized diagnostic-friendly implementations ready for downstream slices.
- `tests/test_slot_filling.py`, `tests/test_intake_task.py` — Green proof suite locking the S02 boundary.
