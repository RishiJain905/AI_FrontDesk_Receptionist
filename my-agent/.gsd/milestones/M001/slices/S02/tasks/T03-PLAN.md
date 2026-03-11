---
estimated_steps: 5
estimated_files: 3
---

# T03: Implement LiveKit IntakeTask with tool-driven state updates and completion guards

**Slice:** S02 — Slot-Filling Intake and Background Classification
**Milestone:** M001

## Description

Wrap the deterministic S02 core in a real LiveKit `AgentTask` so the roadmap’s slot-filling approach is proven with multi-turn evals. This task turns the tracker/policy/classifier primitives into conversational behavior with explicit tool-call boundaries and strict completion rules.

## Steps

1. Implement `src/conversation/intake_task.py` as a LiveKit `AgentTask` that owns a `SlotTracker`, receives policy/classifier collaborators, and exposes a task-level completion boundary based on confirmed required slots.
2. Add clearly documented function tools for recording slot candidates, confirming a slot, rejecting/clearing a slot, and any grouped slot intents needed for reliable extraction; keep docstrings explicit about when each tool should and should not be used.
3. Wire tool handlers to update tracker state and recompute required-slot completion using `IntakePolicy`, ensuring low-confidence/tentative values require confirmation before task completion.
4. Run `tests/test_intake_task.py`, then refine task prompts/tool docstrings or state wiring until the multi-turn evals prove adaptive questioning and no premature completion.
5. Keep completion guards explicit and safe: task completion should happen once, only after all currently required slots are confirmed, and tests should continue to expose the blocking state when not yet complete.

## Must-Haves

- [ ] The task uses function tools to mutate structured slot state rather than relying on prompt-only extraction.
- [ ] Multi-turn eval tests pass for partial-volunteer and tentative-confirmation paths, and task completion is blocked until policy-required slots are confirmed.

## Verification

- `uv run pytest tests/test_intake_task.py -q`
- `uv run ruff check src/conversation/intake_task.py tests/test_intake_task.py`

## Observability Impact

- Signals added/changed: Task state transitions become inspectable through the tracker and eval event stream; completion semantics are surfaced by explicit task state rather than hidden prompt assumptions.
- How a future agent inspects this: Run the intake-task eval tests and inspect event ordering/tool use when a flow regresses.
- Failure state exposed: Premature completion, missing confirmations, or tool-call gaps appear as deterministic test failures tied to the task boundary.

## Inputs

- `src/conversation/slot_tracker.py`, `src/conversation/intake_policy.py`, `src/classification/live_classifier.py` — Deterministic state/policy/classifier core from T02.
- `tests/test_intake_task.py` — Multi-turn LiveKit proof target defining the task’s expected behavior.

## Expected Output

- `src/conversation/intake_task.py` — LiveKit `IntakeTask` implementing tool-driven adaptive intake with strict completion guards.
- `tests/test_intake_task.py` — Passing eval coverage for the slice’s conversational behavior boundary.
