# GSD State

**Active Milestone:** M001 — HVAC After-Hours Voice Agent
**Active Slice:** S03 — Conversation Controller, Prompts, and Safety Branch
**Active Task:** T01 — pending
**Phase:** S02 complete; ready to begin S03 implementation and safety-handoff proof work

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

## Blockers

- None.

## Next Action

Start S03 by wiring `IntakeTask` into the real HVAC conversation controller, adding prompts/opening flow, and proving immediate safety handoff behavior against the now-green S02 proof boundary (`tests/test_slot_filling.py`, `tests/test_intake_task.py`).
