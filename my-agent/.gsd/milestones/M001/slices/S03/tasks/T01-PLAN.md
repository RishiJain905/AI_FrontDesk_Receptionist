---
estimated_steps: 4
estimated_files: 3
---

# T01: Lock S03 behavior with failing prompt and controller evals

**Slice:** S03 — Conversation Controller, Prompts, and Safety Branch
**Milestone:** M001

## Description

Create the RED proof boundary for S03 before implementation. The tests must replace the starter-template coverage with slice-specific assertions that prove the after-hours opening, clean intake close, and explicit safety handoff event required by the roadmap.

## Steps

1. Add `tests/test_prompts.py` with direct assertions for `build_system_prompt(config)`, `SAFETY_INSTRUCTIONS`, and `CLOSING_INSTRUCTIONS`, covering after-hours identity, emergency guidance language, and concise close instructions.
2. Add `tests/test_conversation_controller.py` with LiveKit eval tests that start the planned HVAC controller, assert the opening greeting intent, assert an `agent_handoff` event when danger keywords appear, and judge the safety reply for emergency-first guidance plus minimum viable capture.
3. Rewrite `tests/test_agent.py` to remove starter-assistant expectations and instead assert that the entrypoint imports/constructs the planned S03 controller boundary rather than the generic template assistant.
4. Run the named S03 pytest command and confirm the failure is due to missing S03 runtime modules/wiring, not weak or placeholder assertions.

## Must-Haves

- [ ] Tests name the real S03 artifacts (`conversation.prompts`, `conversation.conversation_controller`, and the entrypoint wiring) so missing implementation fails honestly at collection or assertion time.
- [ ] At least one test asserts an explicit LiveKit handoff event rather than inferring safety mode only from assistant wording.
- [ ] At least one test asserts clean close behavior on the normal path without weakening S02 completion semantics.

## Verification

- `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_agent.py`
- Expected initial result: FAIL because the S03 runtime and entrypoint wiring are not implemented yet, while the tests themselves collect and express the intended slice contract.

## Observability Impact

- Signals added/changed: Test-level visibility for prompt content, explicit handoff events, and entrypoint composition boundary.
- How a future agent inspects this: Run the named pytest command and inspect whether failures come from prompt content, handoff event absence, or entrypoint wiring mismatch.
- Failure state exposed: Missing `agent_handoff` events, wrong opening/closing intent, or stale starter assistant wiring becomes immediately visible.

## Inputs

- `src/conversation/intake_task.py` — authoritative S02 intake behavior that S03 must preserve and wrap rather than duplicate.
- `tests/test_intake_task.py` — proven event-level LiveKit eval style for function-call ordering and guarded completion.
- `src/agent.py` — current starter entrypoint shape that must keep its LiveKit server/session scaffolding while swapping in the HVAC controller.
- S03 research summary — requires `session.update_agent(SafetyAgent(...))`, `on_enter()` usage, and chat context preservation across handoff.

## Expected Output

- `tests/test_prompts.py` — RED prompt-contract tests for system, safety, and closing instructions.
- `tests/test_conversation_controller.py` — RED controller eval tests proving greeting, handoff, and safety-first response requirements.
- `tests/test_agent.py` — RED entrypoint-composition test no longer tied to starter-template friendliness behavior.
