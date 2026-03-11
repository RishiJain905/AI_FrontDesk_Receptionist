# S03: Conversation Controller, Prompts, and Safety Branch — UAT

**Milestone:** M001
**Written:** 2026-03-11

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: S03 is primarily a runtime-behavior slice, so the most trustworthy proof is a mix of real LiveKit `AgentSession` evals for greeting/handoff/closing behavior plus artifact-driven AST verification that `src/agent.py` starts the HVAC controller instead of the starter assistant.

## Preconditions

- Project dependencies are installed via `uv`.
- The environment can construct the configured LiveKit inference models used by the tests.
- `src/agent.py`, `src/conversation/prompts.py`, and `src/conversation/conversation_controller.py` contain the S03 runtime wiring.
- The repository root is the current working directory.

## Smoke Test

Run:

- `uv run pytest tests/test_prompts.py tests/test_conversation_controller.py tests/test_agent.py -q`

Passing this command confirms the prompt surfaces exist, the controller handles greeting and safety routing, and the entrypoint is no longer wired to the starter assistant.

## Test Cases

### 1. After-hours greeting opens as the HVAC line

1. Run `uv run pytest tests/test_conversation_controller.py -q`.
2. Inspect the passing case `test_controller_opens_as_after_hours_hvac_assistant`.
3. **Expected:** The controller responds like North Star HVAC's after-hours line, offers help with the heating/cooling issue, and does not present itself as a generic AI assistant.

### 2. Danger keywords trigger explicit safety handoff

1. Run `uv run pytest tests/test_conversation_controller.py -q`.
2. Inspect the passing case `test_controller_emits_explicit_handoff_event_for_danger_keywords`.
3. **Expected:** The run contains a real LiveKit `agent_handoff` event whose `new_agent` is `SafetyAgent`, and the assistant reply gives emergency guidance before minimum intake capture.

### 3. Normal-path intake closes cleanly without false completion

1. Run `uv run pytest tests/test_conversation_controller.py -q`.
2. Inspect the passing case `test_controller_closes_cleanly_after_normal_intake_completion`.
3. **Expected:** The controller performs the expected intake tool calls, then closes concisely only after required details have been captured.

### 4. Entrypoint composes the validated HVAC controller

1. Run `uv run pytest tests/test_agent.py -q`.
2. Inspect the passing AST assertions.
3. **Expected:** `src/agent.py` imports `load_config` and `HVACConversationController`, defines `build_runtime_agent()`, and calls `session.start(agent=build_runtime_agent(), ...)` without the starter `Assistant` wiring.

## Edge Cases

### Greeting-only turn does not pollute slot state

1. Run `uv run pytest tests/test_conversation_controller.py -q`.
2. Focus on the greeting-only scenario.
3. **Expected:** The agent answers naturally as the business line and asks for intake details without inferring or recording name/phone/issue from a bare greeting.

## Failure Signals

- `ModuleNotFoundError` for `conversation.prompts` or `conversation.conversation_controller`
- `test_controller_emits_explicit_handoff_event_for_danger_keywords` fails because no `agent_handoff` event is present
- `test_agent_entrypoint_starts_session_with_runtime_agent_factory_not_template_assistant` fails because `Assistant(` still appears in `src/agent.py`
- Greeting behavior sounds generic or claims to be an AI assistant
- Normal close occurs before all required intake data is captured

## Requirements Proved By This UAT

- R001 — Proves the after-hours HVAC controller opens correctly, continues adaptive intake through the real controller/runtime path, and closes only after required slot capture.
- R003 — Proves danger keywords trigger an explicit `SafetyAgent` handoff with emergency-first guidance.
- R010 — Proves S03 added executable pytest coverage for the prompt/controller/entrypoint behavior paths it owns.

## Not Proven By This UAT

- R005 — No CRM write is exercised here.
- R006 — No owner SMS alert is exercised here.
- R007 — No after-hours time gate is exercised here.
- R009 — Partial-call finalization and failure isolation are not exercised here.
- Human phone-call experience through LiveKit console/SIP is not proven by this UAT.

## Notes for Tester

This UAT is intentionally test-driven rather than human-call-driven. If the danger-path test fails, inspect `src/conversation/conversation_controller.py` first, especially the `llm_node(...)` routing and `handoff_to_safety` tool exposure. If the entrypoint test fails, inspect `build_runtime_agent()` in `src/agent.py` before changing the tests.
