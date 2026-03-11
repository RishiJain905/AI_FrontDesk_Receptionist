# S05 — Research

**Date:** 2026-03-11

## Summary

S05 owns the runtime gap between the already-proven conversation pieces and the milestone’s operational promises. Based on the current codebase, this slice primarily needs to deliver **R007 (after-hours gate)** and **R009 (graceful failure handling / partial-call finalization)** while materially supporting **R005 (CRM persistence)** by wiring the existing GoHighLevel and Twilio boundaries into a real call-finalization path.

The safest implementation shape is an **idempotent lifecycle coordinator** attached to `AgentSession` events rather than more prompt logic. LiveKit 1.4.4 already exposes the exact hooks S05 needs: `conversation_item_added` for transcript capture, `user_state_changed` / `close` for hang-up detection, and `generate_reply(...)` for the missing inbound greeting. The current controller and integration layers are reusable, but there are two important contract gaps that will block a clean slice unless handled explicitly: **`BusinessConfig` does not yet carry after-hours window fields**, and **`CallIntakeRecord` has no dedicated caller-ID / confirmation field for the R009 fallback-phone requirement**.

Timezone handling should stay with stdlib `zoneinfo`, but on this Windows dev environment that is risky unless `tzdata` is declared: the current virtualenv has `livekit-agents==1.4.4`, `httpx==0.28.1`, and **no installed `tzdata` package**. That makes the after-hours gate testable in code but potentially fragile on machines without system IANA data. S05 should therefore treat `ZoneInfo("America/Toronto")` as the implementation path and explicitly defend against missing timezone data during runtime and test setup.

## Recommendation

Implement S05 around a new `CallLifecycle` object that is created in `src/agent.py` and owns these responsibilities:

1. **Gate first** using a pure, injectable `is_after_hours(config, now=...)` helper.
2. **Start the existing `HVACConversationController` unchanged** and subscribe to session events before/around `session.start(...)`.
3. **Assemble transcript incrementally** from `conversation_item_added` events instead of reconstructing history later.
4. **Finalize exactly once** from `close` (and optionally observe `user_state_changed -> away` for diagnostics only), deriving `call_status=complete|partial` from controller/task state.
5. **Build the final record from existing typed surfaces** (`latest_classification`, `handoff_state`, `last_completed_intake_summary`, slot snapshots) rather than duplicating extraction logic.
6. **Call CRM and SMS independently** via `CrmService` / `AlertService`, logging `IntegrationError.to_dict()` on failure and setting `record.sms_sent = True` only after a successful alert send.
7. **Add direct unit coverage** for the overnight gate and a lifecycle test seam that can simulate normal completion, early close, CRM failure, and SMS failure without requiring real telephony.

This keeps S05 aligned with prior slice decisions: controller state stays authoritative, provider logic stays behind protocols, and post-call work remains asynchronous / isolated from the voice turn path.

## Don’t Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Normal vs safety intake state | `HVACConversationController.current_mode`, `latest_classification`, `handoff_state`, `last_completed_intake_summary` | S03 already exposed these as the inspectable runtime truth; duplicating flags in S05 will drift. |
| Required-slot completion status | `IntakeTaskResult` and `SlotTracker` semantics from S02 | These already encode missing / tentative / confirmed state and should drive partial-vs-complete finalization. |
| CRM note formatting | `services.crm.mappers.build_contact_note()` | S04 already locked deterministic note layout in tests; lifecycle code should feed it finalized fields, not reformat text. |
| Owner SMS formatting and skip logic | `TwilioSmsService.send_owner_sms()` + `build_owner_alert_text()` | Duplicate-prevention and concise formatting are already implemented and tested. |
| Provider isolation | `CrmService`, `AlertService`, and `IntegrationError.to_dict()` | This is the clean boundary for R005/R009; avoid concrete-provider logic in the lifecycle. |
| Transcript capture | `session.on("conversation_item_added")` | LiveKit provides a committed-message event with `text_content` and `interrupted`; this is more reliable than scraping logs or prompt history afterward. |
| Timezone conversion | `zoneinfo.ZoneInfo` | Matches D005 and handles DST/fold correctly when backed by timezone data. |

## Existing Code and Patterns

- `src/conversation/conversation_controller.py` — Best reuse point for call-finalization state. `HVACConversationController` already surfaces `current_mode`, `latest_classification`, `handoff_reason`, `handoff_state`, and `last_completed_intake_summary`; S05 should consume these directly.
- `src/conversation/intake_task.py` — The authoritative structured intake boundary. `IntakeTaskResult.slots`, `missing_required_slots`, and `tentative_slots` are the cleanest source for deciding `complete` vs `partial`.
- `src/classification/live_classifier.py` — Already provides deterministic live danger / urgency / issue signals. S05 should not reclassify turns inline during the call.
- `src/services/crm/ghl_service.py` — `upsert_contact()` already performs search/create-or-update/note attach in one async path. Lifecycle code should treat it as one independent post-call operation.
- `src/services/alerts/sms_service.py` — Already enforces `notify_owner` / `sms_sent` skip semantics. S05 only needs to set `notify_owner` correctly and flip `sms_sent` after success.
- `src/services/crm/mappers.py` — Structured CRM note currently depends on `call_status`, classification fields, `callback_time`, `summary`, `transcript`, and `ai_summary`; S05 must populate those before persistence.
- `src/utils/errors.py` — Use `IntegrationError.to_dict()` for structured logging rather than ad hoc exception strings.
- `src/agent.py` — Keeps the starter bootstrap shape and exposes `build_runtime_agent()`, but it currently has **no lifecycle wiring, no after-hours gate, and no initial greeting trigger**.
- `tests/test_conversation_controller.py` — Confirms the normal/safety controller boundary is already working; S05 should add lifecycle tests around it rather than weakening these proofs.
- `tests/test_ghl_service.py` / `tests/test_sms_service.py` — Lock outbound payload contracts already; S05 should reuse these providers, not add new HTTP code.

## Constraints

- **`BusinessConfig` does not currently include after-hours start/end fields.** `src/hvac_types/business_config.py` only has business identity, timezone, owner phone, service area, and keyword lists. R007 says the time window is configured; S05 must either extend the config contract or accept a hardcoded default that partially violates R008.
- **`CallIntakeRecord` cannot cleanly represent the R009 fallback-phone nuance yet.** It has `phone_number`, but no `caller_id`, no phone confirmation flag, and no per-slot confidence. If S05 falls back to caller ID when callback number is missing, that fact is currently lossy unless the type contract is extended or the distinction is recorded in `notes` / `summary`.
- **The runtime environment currently lacks `tzdata`.** Python `zoneinfo` docs note that Windows often lacks system IANA timezone data; this environment confirms `tzdata` is not installed, so `ZoneInfo(config.timezone)` can fail on some machines unless that dependency is declared.
- **`src/agent.py` currently loads only `.env.local`.** Tests load both `.env.local` and `.env`, but runtime boot does not. If S05 adds GHL/Twilio runtime env wiring, boot-time behavior should be explicit.
- **There is no existing final-classification contract.** The roadmap expects `FinalClassifier` / `FinalClassification`, but the current repo has no such module or dataclass yet. S05 should keep this seam small and typed.
- **Inbound callers are not greeted automatically yet.** LiveKit’s telephony docs recommend `await session.generate_reply(instructions="Greet the user and offer your assistance.")` after `session.start(...)`; without that, SIP callers may hear silence until they speak.

## Common Pitfalls

- **Finalizing from multiple event paths without a guard** — `user_state_changed`, `participant_disconnected`, and `close` can all point at the same end-of-call outcome. Use a single `finalize_once()` gate (lock / boolean / task handle) so CRM writes and SMS sends cannot double-fire.
- **Deriving transcript from prompts or tool text instead of committed messages** — `conversation_item_added` is the durable source. Ignore controller instruction churn and only store committed user/assistant content in order.
- **Treating `user_state_changed -> away` as the sole hang-up signal** — keep `close` as the authoritative finalization trigger; use `away` for observability or early marking only.
- **Hardcoding 5 PM–9 AM directly in gate logic** — the requirement says configured timezone / hours. If config is not extended now, S05 will ship a hidden product rule outside the config contract.
- **Using naive datetimes or string comparison for the overnight window** — convert `now` into the configured timezone first, then compare `datetime.time` values with an overnight-aware branch (`start <= end` vs `start > end`).
- **Sending SMS before mutating lifecycle state** — `TwilioSmsService` prevents duplicates per call object, but S05 still needs to set `record.sms_sent = True` only after a successful send or retries can re-alert the owner.
- **Re-implementing contact/note or SMS formatting in the lifecycle** — S04 already proved these boundaries; lifecycle orchestration should populate the record and delegate.

## Open Risks

- **Config contract gap for R007:** after-hours window fields are missing from `BusinessConfig` and `HVAC_DEMO_CONFIG`, so S05 may need to expand S01’s type surface before it can implement a truly config-driven gate.
- **R009 data-model gap:** fallback-to-caller-ID with `confirmed=false` is not representable cleanly in the current `CallIntakeRecord` contract.
- **Operational env gap:** the repo currently shows LiveKit dotenv wiring but no runtime naming / loading convention for GoHighLevel and Twilio credentials in `src/agent.py`.
- **Timezone data portability:** `zoneinfo` is the correct API, but Windows deployments may fail without `tzdata` installed.
- **Final-summary scope creep:** the roadmap wants `summary_builder` and `FinalClassifier`, but no existing interface specifies whether they are deterministic, LLM-backed, or both. Keep S05 small enough that CRM/SMS finalization works even if summary quality is initially minimal.
- **Current S03 fragility still matters:** S03 reported intermittent `tests/test_intake_task.py::test_tentative_slot_requires_explicit_confirmation_before_completion` behavior. S05 should avoid lifecycle logic that depends on brittle function-call ordering beyond `done()` / result state.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LiveKit Agents | installed skill `livekit-agents` | installed |
| Twilio | `sickn33/antigravity-awesome-skills@twilio-communications` | available (highest install count found: 360) |
| GoHighLevel | none found via `npx skills find "GoHighLevel"` | none found |

## Sources

- LiveKit session lifecycle events, including `conversation_item_added`, `user_state_changed`, and `close`, confirm the event hooks S05 can use for transcript assembly and finalization (source: LiveKit Agents docs — https://docs.livekit.io/agents/logic/sessions and https://docs.livekit.io/agents/build/events).
- LiveKit telephony docs recommend calling `session.generate_reply(...)` after `session.start(...)` to greet inbound callers, which closes a current runtime gap in `src/agent.py` (source: LiveKit Agents docs — https://docs.livekit.io/agents/start/telephony).
- LiveKit tool/handoff docs confirm the current S03 pattern of returning an `Agent` from a function tool and preserving `chat_ctx` across handoff (source: LiveKit Agents docs — https://docs.livekit.io/agents/build/tools and https://docs.livekit.io/agents/logic/agents-handoffs).
- Python `zoneinfo` docs confirm DST/fold support and warn that Windows often needs `tzdata` when system IANA timezone data is absent (source: Python docs — https://docs.python.org/3/library/zoneinfo.html).
- `src/conversation/conversation_controller.py` exposes the diagnostics S05 should treat as authoritative controller state.
- `src/conversation/intake_task.py` defines the durable structured intake result and completion guards that should drive partial-vs-complete finalization.
- `src/services/crm/ghl_service.py`, `src/services/crm/mappers.py`, and `src/services/alerts/sms_service.py` already provide the provider-backed persistence/alert boundaries that S05 should orchestrate rather than replace.
- `src/hvac_types/business_config.py` and `src/hvac_types/call_intake_record.py` reveal the two main contract gaps for S05: missing time-window config and missing explicit caller-ID / confirmation fields.
