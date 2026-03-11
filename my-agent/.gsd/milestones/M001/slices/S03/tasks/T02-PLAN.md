---
estimated_steps: 5
estimated_files: 5
---

# T02: Implement prompts and the HVAC conversation controller with safety handoff

**Slice:** S03 — Conversation Controller, Prompts, and Safety Branch
**Milestone:** M001

## Description

Implement the actual S03 runtime surfaces: prompt builders, a thin `HVACIntakeAgent` that preserves S02 intake semantics, and a `SafetyAgent` that takes over immediately when live classification detects danger. The result should make the RED tests pass without recreating slot logic in prompt prose.

## Steps

1. Create `src/conversation/prompts.py` with `build_system_prompt(config)`, `SAFETY_INSTRUCTIONS`, and `CLOSING_INSTRUCTIONS`, all driven by business config values and phrased for concise voice delivery.
2. Create `src/conversation/conversation_controller.py` with `HVACIntakeAgent` and `SafetyAgent`, making the normal controller a thin orchestration layer over `IntakeTask` / `LiveClassifier` rather than a second intake implementation.
3. Implement explicit danger-triggered handoff wiring that uses `session.update_agent(SafetyAgent(...))`, records an inspectable handoff reason/current mode surface, and preserves `chat_ctx` across the transition.
4. Implement safety-path behavior so the first safety reply gives calm emergency guidance, then asks only for minimum viable fields aligned with S02 danger policy instead of returning to the full normal script.
5. Export the new prompt/controller surfaces via `src/conversation/__init__.py` as needed and iterate until the S03 prompt/controller tests pass while `tests/test_intake_task.py` remains green.

## Must-Haves

- [ ] `HVACIntakeAgent` reuses `IntakeTask` and `LiveClassifier`; it must not duplicate slot-state mutation or completion rules in separate controller logic.
- [ ] Safety handoff is an explicit runtime control transfer with preserved context, not just prompt text that says to behave differently.
- [ ] The normal controller still closes cleanly only after the underlying intake task actually completes.
- [ ] Safety mode limits follow-up collection to minimum viable data and keeps emergency guidance first.

## Verification

- `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_intake_task.py`
- Expected result: PASS, proving prompt content, handoff event behavior, and no regression to the S02 guarded-intake boundary.

## Observability Impact

- Signals added/changed: Inspectable controller attributes for latest classification, current mode, and handoff reason/state; prompt-builder output becomes directly testable.
- How a future agent inspects this: Import controller/prompt modules in tests or REPL and inspect runtime state after eval turns.
- Failure state exposed: Whether failure came from prompt composition, danger detection, context-preserving handoff wiring, or normal close gating becomes localized to stable module boundaries.

## Inputs

- `tests/test_prompts.py` — prompt contract to satisfy.
- `tests/test_conversation_controller.py` — event-level handoff/greeting/closing behavior contract.
- `src/conversation/intake_task.py` — existing deterministic intake engine that must stay authoritative.
- `src/classification/live_classifier.py` and `src/conversation/intake_policy.py` — typed danger and minimum-capture policy surfaces the controller should consume directly.

## Expected Output

- `src/conversation/prompts.py` — config-driven prompt and instruction surfaces for the controller and safety branch.
- `src/conversation/conversation_controller.py` — thin HVAC controller and dedicated safety agent with explicit handoff behavior.
- `src/conversation/__init__.py` — exports for downstream entrypoint/tests.
