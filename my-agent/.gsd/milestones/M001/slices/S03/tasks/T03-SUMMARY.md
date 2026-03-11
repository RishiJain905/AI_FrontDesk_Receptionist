---
id: T03
parent: S03
milestone: M001
provides:
  - Runnable LiveKit entrypoint now composes validated HVAC controller runtime instead of the starter assistant, and console/eval text-path routing now proves greeting-only and danger-handoff behavior through the real controller.
key_files:
  - src/agent.py
  - src/conversation/conversation_controller.py
  - tests/test_agent.py
  - tests/test_conversation_controller.py
key_decisions:
  - Added a `build_runtime_agent()` factory in `src/agent.py` so config loading and controller composition stay separate from later S05 lifecycle orchestration.
  - Enforced greeting-only and danger routing in `HVACConversationController.llm_node(...)` because `AgentSession.run(...)` bypasses `on_user_turn_completed` for console/eval text turns.
patterns_established:
  - Prove entrypoint composition with AST checks that verify validated-config factory wiring, not just imports.
  - For LiveKit console/eval coverage, gate available tools per turn in `llm_node(...)` so first-turn routing is visible before the model can choose inherited intake tools.
observability_surfaces:
  - tests/test_agent.py AST composition checks; tests/test_conversation_controller.py handoff/message assertions; controller state attributes current_mode/latest_classification/handoff_reason/handoff_state/last_completed_intake_summary
duration: 1h17m
verification_result: passed
completed_at: 2026-03-11T18:07:16.744170-04:00
blocker_discovered: false
---

# T03: Rewire the entrypoint to the HVAC controller and prove console-path composition

**Replaced the starter entrypoint wiring with a validated HVAC controller factory and closed the console/eval composition gap by enforcing first-turn greeting/safety routing inside the real controller.**

## What Happened

`src/agent.py` was rewritten to remove the scaffold `Assistant` usage while preserving the existing LiveKit bootstrap shape: dotenv loading, `AgentServer`, `prewarm`, session model setup, `room_options`, and `ctx.connect()` all remain intact. The only composition change is that session startup now calls `build_runtime_agent()`, which loads validated business config through `load_config()` and returns `HVACConversationController(config=runtime_config)`.

While driving the required verification, the remaining S03 failures exposed a real runtime mismatch: `AgentSession.run(...)` for console/eval text turns does not pass through `on_user_turn_completed`, so greeting-only and danger routing that looked correct in controller hooks was not actually governing the tested path. I fixed that at the controller boundary instead of patching tests. `HVACConversationController.llm_node(...)` now inspects the latest user transcript, injects turn-specific instructions into the current chat context, suppresses tools for greeting-only openers, and limits danger turns to `handoff_to_safety` so the model cannot burn tool steps on inherited intake calls before the handoff.

I also updated the controller eval to assert explicit handoff existence plus safety-first assistant behavior without over-constraining event order, since the observed LiveKit run result records the safety reply before the recorded `agent_handoff` event in this tool-return handoff path.

## Verification

Ran fresh slice verification and confirmed all passed:

- `uv run pytest tests/test_agent.py tests/test_prompts.py tests/test_conversation_controller.py -q` → `8 passed`
- `uv run pytest tests/test_intake_task.py -q` → `3 passed`
- `uv run ruff check src/ tests/` → `All checks passed!`

Behavior confirmed by the passing tests includes:
- `src/agent.py` starts the session through validated HVAC controller composition, not template assistant wiring.
- Greeting-only console/eval turns open as the after-hours HVAC line without polluting intake slots.
- Danger turns emit an explicit `agent_handoff` to `SafetyAgent` and produce emergency-first guidance.
- Normal intake close behavior still passes its existing S03 eval.

## Diagnostics

Future inspection path:

- `uv run pytest tests/test_agent.py tests/test_prompts.py tests/test_conversation_controller.py`
- `uv run pytest tests/test_intake_task.py`
- Inspect `src/agent.py` for `build_runtime_agent()` if entrypoint composition regresses.
- Inspect `src/conversation/conversation_controller.py` if console/eval text turns start ignoring greeting-only or danger routing again; the key seam is `HVACConversationController.llm_node(...)`.

Useful observable surfaces remain:
- AST-visible entrypoint composition in `tests/test_agent.py`
- Runtime handoff/message assertions in `tests/test_conversation_controller.py`
- Controller diagnostics on `current_mode`, `latest_classification`, `handoff_reason`, `handoff_state`, and `last_completed_intake_summary`

## Deviations

Adjusted the danger-turn controller eval to require an explicit handoff event plus safety-first reply, without requiring the handoff event to appear before the reply. This was an SDK-observed ordering detail, not a change to the slice intent.

## Known Issues

None.

## Files Created/Modified

- `src/agent.py` — removed scaffold assistant composition, added validated `build_runtime_agent()` factory, and kept the LiveKit bootstrap shape intact.
- `src/conversation/conversation_controller.py` — added turn-time routing in `llm_node(...)`, greeting-only tool suppression, and handoff-only danger gating for console/eval parity.
- `tests/test_agent.py` — upgraded AST coverage to assert validated-config factory wiring into session startup.
- `tests/test_conversation_controller.py` — aligned runtime assertions with the real handoff/message event behavior while preserving explicit handoff proof.
- `.gsd/DECISIONS.md` — recorded the turn-time routing decision for console/eval parity.
- `.gsd/milestones/M001/slices/S03/S03-PLAN.md` — marked T03 complete.
