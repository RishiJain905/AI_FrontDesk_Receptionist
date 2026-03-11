# M001 / S03 — Research

**Date:** 2026-03-11

## Summary

S03 primarily owns **R001 After-Hours Voice Intake** and **R003 Safety / Emergency Branch**, and it also supports **R002 Adaptive Slot-Filling Conversation** by making sure the new controller layer does not undo the deterministic intake behavior already proven in S02. The safest path is to treat S02's `IntakeTask`, `SlotTracker`, and `LiveClassifier` as the authoritative runtime for intake state, and keep S03 focused on three things only: the opening greeting, the safety handoff, and the clean close behavior.

LiveKit Agents 1.4.4 already supports the core mechanics S03 needs. The SDK and docs confirm that `AgentTask` is an `Agent`, `session.update_agent(...)` is valid for mid-call handoff, `on_enter()` is the right place for a spoken opening or transfer message, and the eval helpers can assert `agent_handoff` events directly. The biggest hidden implementation constraint is **context preservation**: by default, each new agent or task starts with fresh LLM history unless `chat_ctx` is passed into the new `Agent`/`AgentTask` constructor. If S03 forgets that, the `SafetyAgent` will lose conversational continuity right when the call becomes safety-critical.

## Recommendation

Build S03 as a **thin orchestration layer over S02**, not as a second intake implementation.

Recommended approach:

1. **Keep `IntakeTask` authoritative for slot mutation and completion guards.**
   - Reuse its function tools, same-turn confirmation guard, and live classification outputs.
   - Do not move slot state into prompt prose or re-ask logic into `HVACIntakeAgent`.

2. **Make `HVACIntakeAgent` as thin as possible.**
   - Best-fit option: have `HVACIntakeAgent` extend or wrap `IntakeTask`, because `AgentTask` already subclasses `Agent` in the installed SDK.
   - If the roadmap boundary needs a plain `Agent`, make it an immediate controller that greets on `on_enter()` and then delegates into an `IntakeTask(chat_ctx=self.chat_ctx)` instead of duplicating intake logic.

3. **Make danger handoff an explicit, testable runtime event.**
   - Use `session.update_agent(SafetyAgent(...))` to satisfy the milestone decision.
   - Trigger it from a dedicated tool/hook path that fires as soon as the live classifier flags danger; do not rely on a vague prompt instruction like “switch to safety mode.”
   - Preserve conversation context during handoff with `chat_ctx=self.chat_ctx` (or equivalent explicit context assembly).

4. **Keep `SafetyAgent` narrow and calm.**
   - First response: emergency guidance from config (`emergency_instructions`) with concise, phone-friendly language.
   - Second priority: minimum viable capture only, aligned with S02 danger-minimum policy.
   - Avoid falling back into the full normal intake script once danger is detected.

5. **Replace the starter eval focus with slice-specific evals.**
   - Add tests that assert opening greeting intent, immediate handoff on danger keywords, and safety-first reply content.
   - Use LiveKit's `is_agent_handoff` / `contains_agent_handoff` assertions rather than inferring a handoff from wording alone.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Adaptive slot collection and guarded completion | `src/conversation/intake_task.py` | It already has tool-only state mutation, deterministic per-turn recommendations, and `complete_intake()` blocking logic that protects R002. |
| Live danger detection | `src/classification/live_classifier.py` | It already returns typed `danger_type`, `urgency_level`, `issue_category`, and `address_relevant` without depending on prompt wording. |
| Handoff verification in evals | LiveKit `RunResult.expect.contains_agent_handoff(...)` / `is_agent_handoff(...)` | This gives direct proof that S03 actually switched agents, which is stronger than judging assistant prose. |
| Opening / transfer speech hooks | LiveKit `on_enter()` + `session.generate_reply(...)` | This is the documented place for greetings and post-handoff introduction behavior. |

## Existing Code and Patterns

- `src/agent.py` — Preserve the existing `AgentServer`, `prewarm`, `@server.rtc_session`, `AgentSession(...)`, `session.start(...)`, and `ctx.connect()` structure; S03 should swap the starter `Assistant` for the HVAC controller without breaking the entrypoint shape.
- `src/conversation/intake_task.py` — This is already the real intake engine: it tracks transcript accumulation, recomputes live classification each turn, injects deterministic tool recommendations, and blocks completion until required slots are confirmed.
- `src/conversation/slot_tracker.py` — Reuse this as the only source of truth for missing/tentative/confirmed slots; do not duplicate slot bookkeeping in agent prompts.
- `src/conversation/intake_policy.py` — Use `IntakeMode.DANGER_MINIMUM` and `get_required_slots(...)` for safety-path minimum capture instead of inventing a second safety requirement list.
- `src/classification/live_classifier.py` — Use `danger_detected` / `danger_type` as the branch trigger surface for S03.
- `tests/test_intake_task.py` — Follow this event-level style for S03 tests; it already proves that tool ordering and completion timing are more reliable assertions than prose-only judgments.
- `tests/test_agent.py` — This is still starter-template coverage; S03 should replace or heavily rewrite it so the tests actually prove after-hours greeting, safety handoff, and clean close behavior.

## Constraints

- `src/agent.py` must remain the runnable entrypoint and keep the existing LiveKit server/session wiring shape.
- Installed dependency surface is `livekit-agents==1.4.4`; local inspection confirms `AgentTask` subclasses `Agent` and `AgentSession.update_agent(self, agent)` is available.
- LiveKit docs explicitly state that new agents/tasks start with fresh LLM history unless `chat_ctx` is passed into the new constructor; safety handoff must preserve context deliberately.
- S02 established a fragile but passing stability pattern: deterministic per-turn controller recommendations and the no-same-turn-self-confirm rule. Weakening those instructions risks breaking R002 while implementing S03.
- Local LiveKit evals depend on `.env.local` / `.env` loading via `tests/conftest.py`; S03 verification should continue using the named pytest path instead of assuming shell-exported env vars.

## Common Pitfalls

- **Re-implementing intake logic in `HVACIntakeAgent`** — This would duplicate S02 logic, drift from the tested slot semantics, and likely reintroduce premature completion or repeated questions. Keep the controller thin and reuse `IntakeTask`.
- **Switching to `SafetyAgent` without preserving context** — LiveKit resets LLM conversation history by default for a new agent/task. Pass `chat_ctx` explicitly, or the safety branch will lose what the caller already said.
- **Prompt-only “safety mode” instead of a real handoff** — That may sound okay in manual tests but will not satisfy the milestone proof strategy, which requires an asserted handoff event.
- **Judging safety behavior only from assistant wording** — Use explicit `agent_handoff` event assertions plus message-intent judgments so the tests prove both the control transfer and the spoken safety response.

## Open Risks

- The slice boundary says `HVACIntakeAgent(Agent)` while S02 already delivered `IntakeTask(AgentTask)`. Because `AgentTask` is also an `Agent`, the implementation should resolve this by thin subclassing or immediate delegation; a parallel, fully separate `Agent` implementation would be unnecessary risk.
- The exact trigger surface for danger handoff is not built yet. If the trigger lives only in prose instructions instead of an explicit tool/hook, the handoff may be inconsistent and hard to assert.
- Clean closing behavior still needs to be defined carefully so the normal path does not over-talk after `complete_intake()`, and the safety path does not bury emergency guidance under too much data collection.
- Starter `tests/test_agent.py` currently validates generic friendliness/grounding, not milestone behavior. If left untouched, S03 could appear “tested” while still missing its actual acceptance path.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LiveKit Agents | Installed skill: `livekit-agents` | installed |
| pytest | `bobmatnyc/claude-mpm-skills@pytest` — install with `npx skills add bobmatnyc/claude-mpm-skills@pytest` | available |
| pytest / coverage | `github/awesome-copilot@pytest-coverage` — install with `npx skills add github/awesome-copilot@pytest-coverage` | available |

## Sources

- LiveKit handoffs, `on_enter()`, `session.update_agent(...)`, and context preservation behavior (source: [Agents and handoffs | LiveKit Documentation](https://docs.livekit.io/agents/logic/agents-handoffs))
- LiveKit testing workflow and event assertion model for multi-turn agent behavior (source: [Testing and evaluation | LiveKit Documentation](https://docs.livekit.io/agents/start/testing/))
- `IntakeTask` already centralizes transcript accumulation, live classification refresh, deterministic tool recommendations, and guarded completion (source: local code review of `src/conversation/intake_task.py`)
- `SlotTracker` and `IntakePolicy` already encode the missing/tentative/confirmed semantics and danger-minimum required-slot policy that S03 should reuse (source: local code review of `src/conversation/slot_tracker.py` and `src/conversation/intake_policy.py`)
- The current runtime entrypoint shape to preserve is in `src/agent.py` (source: local code review of `src/agent.py`)
- Existing LiveKit eval patterns for function-call ordering and multi-turn assertions are in `tests/test_intake_task.py` (source: local code review of `tests/test_intake_task.py`)
- The installed LiveKit package exposes direct handoff assertions in the eval helper and confirms the local SDK surface (source: local code review of `.venv/Lib/site-packages/livekit/agents/voice/run_result.py` and local `uv run python` signature inspection)
