---
id: T01
parent: S02
milestone: M001
provides:
  - Failing proof tests that define the S02 slot-tracker, intake-policy, live-classifier, and IntakeTask contract boundary
key_files:
  - tests/test_slot_filling.py
  - tests/test_intake_task.py
key_decisions:
  - Keep the new tests importing planned S02 modules directly so RED state fails on missing implementation surfaces instead of hidden placeholders
patterns_established:
  - S02 proof tests assert deterministic inspection surfaces like missing slots, tentative slots, required-slot completion, classifier outputs, and intake completion events
observability_surfaces:
  - tests/test_slot_filling.py assertions over SlotTracker snapshot and classifier fields
  - tests/test_intake_task.py event expectations over function-tool calls and completion ordering
duration: 35m
verification_result: passed
completed_at: 2026-03-11 16:58 EDT
blocker_discovered: false
---

# T01: Write failing slot-filling and intake-task proof tests

**Added failing S02 proof tests for adaptive slot filling, deterministic classification, and guarded intake completion.**

## What Happened

Created `tests/test_slot_filling.py` to define the expected S02 interfaces and behavior for:
- `conversation.slot_tracker.SlotTracker`
- `conversation.intake_policy.IntakeMode` and `get_required_slots`
- `classification.live_classifier.LiveClassifier`

The unit suite asserts slot-state semantic mapping onto the shipped `SlotStatus` contract, candidate rejection/reset behavior, tentative-slot accessors, required-slot completion checks, policy mode differences, and deterministic danger/urgency/address-relevance classification outcomes.

Created `tests/test_intake_task.py` to define the expected LiveKit eval boundary for `conversation.intake_task.IntakeTask`. The evals cover a caller volunteering partial information up front, tentative values requiring explicit confirmation before completion, and completion being blocked until the remaining required slots are collected.

Kept both tests pointed at the planned S02 modules that do not yet exist so the RED state is honest and future implementation tasks can turn these proofs green without rewriting the targets.

## Verification

Ran:
- `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py`
  - Result: failed during collection with `ModuleNotFoundError: No module named 'classification'` and `ModuleNotFoundError: No module named 'conversation'`
  - This matches the task expectation: failure is due to missing S02 modules/behavior, not syntax or malformed tests.
- `uv run ruff check src/ tests/`
  - Result: passed

## Diagnostics

Future agents can inspect the boundary by reading:
- `tests/test_slot_filling.py` for expected `SlotTracker` snapshot/accessor semantics and `LiveClassifier` output fields
- `tests/test_intake_task.py` for expected `AgentSession` event ordering, tool names, and completion guards

Re-running `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` exposes the current missing implementation surface directly.

## Deviations

None.

## Known Issues

- The S02 runtime modules under `src/conversation/` and `src/classification/` do not exist yet, so the new tests intentionally fail at import time.
- The LiveKit eval tests are structurally written against the intended interface but cannot execute behaviorally until `IntakeTask` and its tools are implemented in later tasks.

## Files Created/Modified

- `tests/test_slot_filling.py` — failing unit proof for slot tracking, intake policy, and live classification semantics
- `tests/test_intake_task.py` — failing LiveKit eval proof for adaptive intake-task behavior and completion guards
- `.gsd/milestones/M001/slices/S02/S02-PLAN.md` — marked T01 complete
