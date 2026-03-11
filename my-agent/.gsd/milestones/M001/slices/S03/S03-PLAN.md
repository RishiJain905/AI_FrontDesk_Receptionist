# S03: Conversation Controller, Prompts, and Safety Branch

**Goal:** Turn the green S02 intake boundary into the real after-hours HVAC conversation controller with a natural opening greeting, immediate safety handoff, and clean close behavior while preserving deterministic slot-filling.
**Demo:** In LiveKit evals and console wiring, the agent opens as an after-hours HVAC assistant, continues adaptive intake through `IntakeTask`, switches immediately to `SafetyAgent` when danger keywords appear, and closes the conversation cleanly without undoing S02 slot semantics.

## Must-Haves

- Opening conversation behavior is config-driven and clearly identifies the agent as the business's after-hours HVAC assistant.
- `HVACIntakeAgent` reuses S02 `IntakeTask` rather than duplicating slot logic or classification behavior.
- Danger detection triggers an explicit `session.update_agent(SafetyAgent(...))` handoff event, preserving chat context.
- `SafetyAgent` delivers concise emergency guidance first, then attempts only minimum viable capture aligned with S02 danger policy.
- Normal-path close behavior remains concise and does not claim completion before `IntakeTask` actually completes.
- `src/agent.py` is rewired from the starter assistant to the S03 HVAC controller without breaking the existing LiveKit server/session entrypoint shape.
- Slice verification proves both R001 and R003 behavior with explicit LiveKit eval assertions, including a handoff event assertion.

## Proof Level

- This slice proves: operational
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_agent.py`
- `uv run pytest tests/test_intake_task.py`
- `uv run ruff check src/ tests/`

## Observability / Diagnostics

- Runtime signals: structured controller state exposed as inspectable agent/task attributes for current mode (`normal` vs `safety`), latest live classification, handoff reason, and last completed-intake summary; prompt-builder output remains deterministic and testable as plain strings.
- Inspection surfaces: `tests/test_conversation_controller.py` event assertions, direct imports of `build_system_prompt()`, `SAFETY_INSTRUCTIONS`, `CLOSING_INSTRUCTIONS`, and runtime inspection of agent/controller attributes in unit tests.
- Failure visibility: failed handoffs surface as missing `agent_handoff` events; prompt regressions surface as direct string/assertion failures; controller regressions remain localizable to prompt builder vs handoff wiring vs `src/agent.py` session composition.
- Redaction constraints: prompts and diagnostics must not log secrets or raw credentials; only business config values already intended for caller speech may appear in prompts/tests.

## Integration Closure

- Upstream surfaces consumed: `src/conversation/intake_task.py`, `src/conversation/slot_tracker.py`, `src/conversation/intake_policy.py`, `src/classification/live_classifier.py`, `src/config/load_config.py`, `src/config/hvac_demo_config.py`, and the S01 HVAC type/config contracts.
- New wiring introduced in this slice: `src/conversation/prompts.py`, `src/conversation/conversation_controller.py`, replacement of the starter `Assistant` in `src/agent.py` with the HVAC conversation controller, and LiveKit eval coverage for greeting/handoff/closing behavior.
- What remains before the milestone is truly usable end-to-end: CRM persistence and SMS alerts (S04), after-hours gate plus lifecycle finalization and transcript assembly (S05), and full milestone hardening/coverage/readme polish (S06).

## Tasks

- [x] **T01: Lock S03 behavior with failing prompt and controller evals** `est:45m`
  - Why: Define the slice stopping condition first so greeting, handoff, and closing behavior are proven at the real runtime boundary instead of inferred later.
  - Files: `tests/test_prompts.py`, `tests/test_conversation_controller.py`, `tests/test_agent.py`
  - Do: Replace the starter agent tests with S03-specific coverage, add prompt-builder tests for the after-hours/system/safety/closing instructions, and add LiveKit eval tests that assert opening greeting intent, explicit safety handoff events, safety-first reply content, and clean close behavior while preserving S02 intake semantics. Keep these tests RED until controller and prompt runtime exists.
  - Verify: `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_agent.py`
  - Done when: Named S03 tests exist, assert the real slice contract, and fail only because the S03 runtime wiring/prompt modules are not implemented yet.
- [x] **T02: Implement prompts and the HVAC conversation controller with safety handoff** `est:1h15m`
  - Why: This is the slice's core product increment: the real after-hours greeting, prompt surfaces, and runtime handoff logic that wraps S02 intake without reimplementing it.
  - Files: `src/conversation/prompts.py`, `src/conversation/conversation_controller.py`, `src/conversation/__init__.py`, `tests/test_prompts.py`, `tests/test_conversation_controller.py`
  - Do: Add config-driven prompt builders/constants, implement `HVACIntakeAgent` as a thin controller over `IntakeTask`/live classification, implement `SafetyAgent` with context-preserving minimal-intake behavior, expose explicit handoff reason/state inspection surfaces, and make the new tests pass without weakening S02 deterministic guards.
  - Verify: `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_intake_task.py`
  - Done when: The S03 controller tests pass, `SafetyAgent` handoff is asserted directly, prompts are deterministic/tested, and S02 intake tests still pass unchanged.
- [x] **T03: Rewire the entrypoint to the HVAC controller and prove console-path composition** `est:45m`
  - Why: The slice is not complete until the runnable entrypoint uses the new controller instead of the generic starter assistant.
  - Files: `src/agent.py`, `tests/test_agent.py`, `src/conversation/conversation_controller.py`
  - Do: Swap the starter `Assistant` for the S03 HVAC controller in the existing LiveKit server/session structure, keep dotenv/prewarm/session setup intact, add or update entrypoint-focused tests that prove the session starts with the HVAC controller shape, and preserve compatibility with later S05 lifecycle wiring.
  - Verify: `uv run pytest tests/test_agent.py tests/test_prompts.py tests/test_conversation_controller.py && uv run ruff check src/ tests/`
  - Done when: `src/agent.py` composes the HVAC controller, starter-template behavior is gone from tests, and the named verification command passes.

## Files Likely Touched

- `src/conversation/prompts.py`
- `src/conversation/conversation_controller.py`
- `src/conversation/__init__.py`
- `src/agent.py`
- `tests/test_prompts.py`
- `tests/test_conversation_controller.py`
- `tests/test_agent.py`
