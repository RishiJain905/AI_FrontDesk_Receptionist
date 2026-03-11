# GSD State

**Active Milestone:** M001 — HVAC After-Hours Voice Agent
**Active Slice:** S03 — recovery / verification blocker
**Active Task:** stabilize post-S03 verification before commit
**Phase:** The required S03 durable artifacts are written and the roadmap is marked complete, but final completion is blocked because a fresh rerun exposed intermittent failure in `tests/test_intake_task.py::test_tentative_slot_requires_explicit_confirmation_before_completion` after the S03 changes.

## Recent Decisions

- D001: Python (not TypeScript) — scaffold is Python; TS type notation in spec translated to dataclasses
- D003: AgentTask with function_tool decorators for slot-filling
- D004: session.update_agent(SafetyAgent()) for safety branch handoff
- D006: httpx async client for GHL and Twilio integrations
- D012: GoHighLevel v2 API with Bearer token
- D013: Subdirectories mapping — `src/hvac_types/` and `src/config/` for typing and config modules
- D014: All `str, Enum` subclasses must override `__str__` to return `self.value` (Python 3.13 compat)
- D015: `load_config()` enforces required non-empty `business_name`, `timezone`, and `owner_phone` at boot
- D016: S02 proof boundary is test-first: imports must target planned `conversation.*` and `classification.*` modules directly so RED failures surface missing runtime modules honestly
- D017: Preserve S01 `SlotStatus.EMPTY/FILLED/CONFIRMED` as storage and expose S02 `missing/tentative/confirmed` semantics through `SlotTracker` helpers
- D018: `IntakeTask` injects deterministic per-turn tool recommendations and reply requirements, and same-turn tentative values may not self-confirm
- D019: Pytest loads `.env.local` first and then `.env` so the named S02 verification command can construct LiveKit inference models after secure local secret collection
- D020: S03 safety proof must assert a real `agent_handoff` event plus safety-response intent
- D021: S03 controller should expose inspectable current mode, latest classification, handoff reason, and completed-intake summary state
- D022: LiveKit handoff events are emitted reliably when a function tool returns the replacement `Agent`
- D023: Console/eval text turns must be routed in `HVACConversationController.llm_node(...)` because `AgentSession.run(...)` bypasses `on_user_turn_completed`
- D024: `src/agent.py` uses `build_runtime_agent()` so validated config loading and controller composition stay separate from later lifecycle wiring

## Blockers

- `tests/test_intake_task.py::test_tentative_slot_requires_explicit_confirmation_before_completion` is flaky on fresh reruns: observed second-turn tool sequences included `confirm_slot + record_slot_candidate + complete_intake`, `confirm_slot + confirm_slot + complete_intake`, and at least one run with no function-call events before the assistant message.
- Because the named slice verification command is not durably green, `git commit -m 'feat(gsd): complete S03'` is blocked for now.

## Next Action

Investigate and stabilize the `IntakeTask` tentative-confirmation path, then rerun the full S03 verification gate before committing. Do not start S04 yet.
