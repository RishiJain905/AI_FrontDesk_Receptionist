# S02: Slot-Filling Intake and Background Classification — Research

**Date:** 2026-03-11
**Slice:** S02 — Slot-Filling Intake and Background Classification
**Risk:** high
**Depends on:** S01

## Requirement Targeting (Active)

This slice directly advances:

- **R002 (primary owner):** Adaptive slot-filling conversation (missing/tentative/confirmed behavior)
- **R004 (primary owner):** Live/background classification for danger + urgency adaptation

This slice materially supports:

- **R001 (supporting):** Core after-hours intake capture quality (name/phone/issue/callback-time logic readiness)
- **R003 (supporting):** Early danger signal detection that will trigger safety handoff in S03

## Skill Selection Notes

- No explicit **GSD Skill Preferences** block was present in system context.
- Relevant installed skill used for methodology: **`livekit-agents`** (project-local).
- Skill discovery was also run for missing technology-specific support (pytest/async testing, slot-filling domain).

## Summary

S02 should be implemented as a **state-first intake core**: a deterministic `SlotTracker` + `IntakePolicy` + lightweight `LiveClassifier`, then wrapped by a LiveKit `AgentTask` (`IntakeTask`) that uses `@function_tool` calls to mutate state and complete only when policy requirements are satisfied. This aligns with LiveKit’s recommended pattern for unordered collection tasks and keeps conversational behavior testable without depending on brittle prompt-only extraction.

The biggest discovery is a **contract vocabulary mismatch** between planned slice language and current S01 types: S01 currently ships `SlotStatus.EMPTY/FILLED/CONFIRMED`, while milestone text and requirements repeatedly refer to `missing/tentative/confirmed`. If this is not normalized in S02 (either by explicit mapping or type update), tests and downstream reasoning will drift.

For reliability, S02 testing should combine (1) pure unit tests for tracker/policy/classifier transitions and (2) `AgentSession` multi-turn evals that explicitly assert function-call behavior and tentative-to-confirmed transitions. LiveKit docs and runtime introspection confirm this is the intended testing shape for task-driven collection.

## Recommendation

Use a layered implementation:

1. **`conversation/slot_tracker.py`**
   - Maintain per-slot `SlotState` + helper APIs:
     - `get_missing_slots()`
     - `get_tentative_slots()`
     - `update_slot(slot_name, value, confidence, confirmed=False)`
     - `all_required_confirmed(required_slots)`
   - Keep it deterministic and framework-agnostic.

2. **`conversation/intake_policy.py`**
   - Define required slots for:
     - normal mode
     - danger mode (minimum viable capture)
   - Add address relevance decision hook from classifier output.

3. **`classification/rules.py` + `classification/live_classifier.py`**
   - Rule-first keyword classifier for live path (<10ms target).
   - Return a structured `LiveClassification` model (danger detected, likely urgency, address relevance, customer-type hint).

4. **`conversation/intake_task.py` (or equivalent module)**
   - `AgentTask` with clear tool docstrings (LiveKit best practice for tool-call reliability).
   - One tool per slot family (record name/phone/issue/callback-time/address, plus confirm/reject flows).
   - Complete task only when policy confirms all required slots.

5. **Tests**
   - Unit tests: tracker transitions, policy required-slot sets, classifier keyword behavior.
   - Agent eval tests: multi-turn path where user volunteers partial info first; assert no premature completion; assert tentative slot gets explicit confirmation before completion.

## Don’t Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|-------------------|------------|
| Multi-turn workflow orchestration in voice agent | `AgentTask` + `@function_tool` (LiveKit) | Native task lifecycle, tool-driven structured capture, and explicit completion semantics |
| Live transcript hooks | `session.on("conversation_item_added")` | Canonical event surface for incremental classification and transcript-aware adaptation |
| Mid-session agent switching (used by S03, produced by S02 signals) | `session.update_agent(...)` | Official handoff mechanism; avoids bespoke control plumbing |
| Agent behavior verification | `AgentSession.run(...)` + `result.expect...` eval pattern | Already used in repo; supports multi-turn + function-call assertions |

## Existing Code and Patterns

- `src/agent.py`
  - Current baseline still generic assistant; this is the integration anchor S03/S05 will wire into.
  - Confirms import style (`from agent import Assistant` in tests) and session setup conventions.

- `tests/test_agent.py`
  - Existing eval test harness uses `AgentSession` and `result.expect.next_event().judge(...)`.
  - Reuse this pattern for S02 multi-turn slot-filling tests.

- `src/hvac_types/slot_state.py`
  - Current enum is `EMPTY/FILLED/CONFIRMED` and dataclass supports `confidence` + `attempts`.
  - This supports tentative confirmation logic, but naming is currently misaligned with roadmap wording.

- `src/config/hvac_demo_config.py`
  - Existing keywords (`safety_keywords`, `no_heat_keywords`, `no_cool_keywords`) provide immediate seed signals for live classifier.

- Runtime SDK introspection (`.venv/Scripts/python`)
  - `livekit-agents==1.4.4`
  - `AgentTask.__await__` is non-reentrant and only valid in specific agent/task contexts.
  - `AgentTask.complete(...)` raises if called twice.

## Constraints

- **Must align with S01 contracts already shipped** (`hvac_types`, `config`), unless a deliberate superseding decision is made.
- **LiveKit API correctness must come from docs/current SDK** (not memory); S02 depends heavily on `AgentTask` and function tools.
- **Task completion is strict**: double-complete raises runtime error; no premature completion if required slots are unresolved.
- **Current `BusinessConfig` does not include a general `urgent_keywords` field**; urgency logic must use existing fields or add a bounded contract extension intentionally.
- **Import/package layout currently uses subpackages (`src/hvac_types`, `src/config`)**; new `src/conversation` / `src/classification` directories should be package-safe (`__init__.py`).

## Common Pitfalls

- **Status vocabulary drift (`missing/tentative` vs `empty/filled`)** — normalize early (mapping layer or enum update) and keep tests explicit.
- **Prompt-only slot filling** — use tools for state mutation; prompts alone will regress silently.
- **Underspecified tool docstrings** — poor descriptions reduce tool-call reliability; document when tool should/shouldn’t be used.
- **Completing task on “all non-empty” instead of “all required confirmed”** — violates R002 skip rule and closes calls too early.
- **Classifier side effects inside event callback** — keep live classifier lightweight and deterministic; no network calls in live path.

## Open Risks

- **RISK-1: Contract mismatch from S01 vs roadmap language**
  - If unresolved, S02 tests/logic can appear “correct” while violating acceptance phrasing.
- **RISK-2: Tool-call reliability for slot extraction**
  - Known high-risk area in roadmap proof strategy; requires targeted eval tests with varied caller utterance shapes.
- **RISK-3: Field shape gap vs eventual CRM payload expectations**
  - `CallIntakeRecord` currently lacks some planned intake fields (e.g., explicit callback time token); S02 should define internal slot schema cleanly so S04/S05 mapping is unambiguous.
- **RISK-4: Danger detection false negatives in colloquial phrasing**
  - Keyword rules need synonym coverage and normalization tests.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LiveKit Agents SDK | `livekit-agents` (project-local installed skill) | **installed** |
| Pytest + asyncio testing | `affaan-m/everything-claude-code@python-testing` | available (1.1K installs) — `npx skills add affaan-m/everything-claude-code@python-testing` |
| Pytest focused workflows | `bobmatnyc/claude-mpm-skills@pytest` | available (446 installs) — `npx skills add bobmatnyc/claude-mpm-skills@pytest` |
| Asyncio patterns | `bobmatnyc/claude-mpm-skills@asyncio` | available (130 installs) — `npx skills add bobmatnyc/claude-mpm-skills@asyncio` |
| Slot-filling domain skill | none clearly relevant found via `npx skills find "slot filling"` | none found |

## Sources

- Agent task pattern and completion via function tools (source: LiveKit docs, https://docs.livekit.io/agents/build/tasks)
- Tool definition reliability guidance / best practices (source: LiveKit docs, https://docs.livekit.io/agents/build/tools)
- Session event hook `conversation_item_added` (source: LiveKit docs, https://docs.livekit.io/agents/build/events)
- Agent handoff mechanism `session.update_agent(...)` (source: LiveKit docs, https://docs.livekit.io/agents/logic/agents-handoffs)
- Multi-turn testing + function-call assertions with `AgentSession.run` (source: LiveKit docs, https://docs.livekit.io/agents/start/testing)
- Local implementation baseline (source: `src/agent.py`, `tests/test_agent.py`, `src/hvac_types/slot_state.py`, `src/config/hvac_demo_config.py`)
- Runtime SDK facts (`livekit-agents==1.4.4`, `AgentTask` method constraints) gathered from local `.venv` introspection commands.
