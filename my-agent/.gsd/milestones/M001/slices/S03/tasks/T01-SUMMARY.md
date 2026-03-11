---
id: T01
parent: S03
milestone: M001
provides:
  - RED proof boundary for S03 prompts, controller handoff, and entrypoint composition
key_files:
  - tests/test_prompts.py
  - tests/test_conversation_controller.py
  - tests/test_agent.py
  - .gsd/milestones/M001/slices/S03/S03-PLAN.md
key_decisions:
  - S03 RED tests import planned runtime modules directly so missing prompt/controller modules fail honestly during collection
  - Entry-point coverage uses AST assertions against src/agent.py so stale starter wiring is caught without depending on unimplemented runtime imports
patterns_established:
  - LiveKit eval coverage for S03 must assert an explicit agent_handoff event and safety-first judged reply, not just wording
observability_surfaces:
  - uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_agent.py
  - uv run pytest tests/test_intake_task.py
  - uv run ruff check src/ tests/
duration: 35m
verification_result: passed
completed_at: 2026-03-11T16:50:07-04:00
blocker_discovered: false
---

# T01: Lock S03 behavior with failing prompt and controller evals

**Added RED S03 tests for prompts, controller handoff/closing behavior, and entrypoint composition, with failures localized to the missing S03 runtime modules and stale wiring boundary.**

## What Happened

I replaced the starter-template `tests/test_agent.py` coverage with an entrypoint composition test that inspects `src/agent.py` and requires `HVACConversationController` wiring instead of the generic `Assistant`.

I added `tests/test_prompts.py` to assert the intended S03 prompt surface directly through `conversation.prompts`, covering after-hours HVAC identity, safety/emergency wording, and concise closing behavior.

I added `tests/test_conversation_controller.py` as the RED proof boundary for the planned controller. Those tests require the real S03 module path `conversation.conversation_controller`, judge the opening greeting intent, assert an explicit `agent_handoff` event to `SafetyAgent` on danger keywords, and require a clean normal-path close after intake completion.

I then ran the named RED verification command and confirmed the expected failure mode is honest: pytest fails at collection because `conversation.prompts` and `conversation.conversation_controller` do not exist yet. That matches the task contract and exposes the missing S03 runtime clearly instead of passing with weak assertions.

## Verification

- Ran `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_agent.py`
  - Result: FAIL as expected.
  - Evidence: collection failed with `ModuleNotFoundError: No module named 'conversation.prompts'` and `ModuleNotFoundError: No module named 'conversation.conversation_controller'`.
  - Interpretation: the RED tests are wired to the real planned S03 artifacts and fail because the runtime is not implemented yet.
- Ran `uv run pytest tests/test_intake_task.py`
  - Result: PASS (`3 passed`).
  - Interpretation: S02 intake behavior remains intact while adding the new RED S03 boundary.
- Ran `uv run ruff check src/ tests/`
  - Result: PASS (`All checks passed!`).

## Diagnostics

Future inspection path:
- Run `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_agent.py`.
- If collection fails on `conversation.prompts` or `conversation.conversation_controller`, the S03 runtime is still missing.
- If collection passes later but assertions fail, the failures should localize to prompt wording, missing `agent_handoff` events, or stale `src/agent.py` composition.
- `tests/test_agent.py` intentionally uses AST inspection so entrypoint wiring regressions remain visible even before full runtime composition is green.

## Deviations

None.

## Known Issues

- `src/conversation/prompts.py` is not implemented yet.
- `src/conversation/conversation_controller.py` is not implemented yet.
- `src/agent.py` still contains the starter `Assistant` wiring, so the rewritten entrypoint contract test will remain red until T03.

## Files Created/Modified

- `tests/test_prompts.py` — RED prompt-contract tests for after-hours system prompt, safety instructions, and closing instructions.
- `tests/test_conversation_controller.py` — RED LiveKit eval tests for greeting intent, explicit handoff event, and clean close behavior.
- `tests/test_agent.py` — replaced starter-template behavior tests with AST-based entrypoint wiring assertions for `HVACConversationController`.
- `.gsd/milestones/M001/slices/S03/S03-PLAN.md` — marked T01 complete.
