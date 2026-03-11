# GSD State

**Active Milestone:** M001 — HVAC After-Hours Voice Agent
**Active Slice:** S02 — Slot-Filling Intake and Background Classification (next)
**Active Task:** Not started
**Phase:** Post-slice closeout (S01 complete)

## Recent Decisions

- D001: Python (not TypeScript) — scaffold is Python; TS type notation in spec translated to dataclasses
- D003: AgentTask with function_tool decorators for slot-filling
- D004: session.update_agent(SafetyAgent()) for safety branch handoff
- D006: httpx async client for GHL and Twilio integrations
- D012: GoHighLevel v2 API with Bearer token
- D013: Subdirectories mapping — `src/hvac_types/` and `src/config/` for typing and config modules
- D014: All `str, Enum` subclasses must override `__str__` to return `self.value` (Python 3.13 compat)
- D015: `load_config()` enforces required non-empty `business_name`, `timezone`, and `owner_phone` at boot

## Blockers

- None.

## Next Action

Begin S02 by implementing slot tracker, intake policy, and live classifier against the S01 contracts, then add multi-turn slot-filling eval tests.
