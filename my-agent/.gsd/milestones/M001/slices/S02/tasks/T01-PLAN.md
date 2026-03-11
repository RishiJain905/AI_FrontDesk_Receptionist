---
estimated_steps: 5
estimated_files: 2
---

# T01: Write failing slot-filling and intake-task proof tests

**Slice:** S02 — Slot-Filling Intake and Background Classification
**Milestone:** M001

## Description

Create the slice’s executable proof boundary before implementation. This task adds the unit and LiveKit eval tests that define what “adaptive slot filling” and “live classification” mean for S02, including tentative confirmation and no-premature-completion behavior.

## Steps

1. Create `tests/test_slot_filling.py` with unit tests covering slot-state semantic mapping, tracker updates, missing/tentative slot accessors, required-slot completion checks, intake-policy mode selection, and live-classifier rule outputs.
2. Create `tests/test_intake_task.py` with `AgentSession` eval tests that exercise a caller volunteering partial information up front, a tentative slot requiring explicit confirmation, and task completion being blocked until required slots are confirmed.
3. Keep the tests pointed at the planned S02 modules (`conversation.slot_tracker`, `conversation.intake_policy`, `classification.live_classifier`, `conversation.intake_task`) so the suite fails for missing implementation rather than silently passing.
4. Run the new slice tests and confirm failure output reflects missing modules/behavior, capturing the true starting point for TDD.
5. Leave the failing tests committed in a clean, readable state with assertions that future tasks can satisfy without rewriting the proof target.

## Must-Haves

- [ ] `tests/test_slot_filling.py` names the exact tracker/policy/classifier interfaces S02 must implement and asserts adaptive-state behavior rather than placeholder existence.
- [ ] `tests/test_intake_task.py` includes multi-turn task assertions for partial-volunteer and tentative-confirmation flows, and initially fails because the implementation is not present yet.

## Verification

- `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py`
- Expected result for this task: failing tests caused by missing S02 modules or unimplemented behavior, not by syntax/import mistakes in the tests themselves.

## Observability Impact

- Signals added/changed: Defines the required diagnostic surfaces by asserting on missing/tentative slots, classifier outputs, and task completion events.
- How a future agent inspects this: Read the new test files and run the named pytest command to see which boundary condition is failing.
- Failure state exposed: Exact requirement gaps become visible as failed assertions/import errors tied to slot tracking, classification, or task completion semantics.

## Inputs

- `tests/test_agent.py` — Existing LiveKit eval style and session harness conventions to mirror for S02 task tests.
- `src/hvac_types/slot_state.py`, `src/hvac_types/classification.py`, `src/config/hvac_demo_config.py` — Existing contracts and config vocabulary the new tests must target.

## Expected Output

- `tests/test_slot_filling.py` — Failing unit proof for tracker, policy, and live-classifier behavior.
- `tests/test_intake_task.py` — Failing LiveKit eval proof for tool-driven adaptive intake behavior.
