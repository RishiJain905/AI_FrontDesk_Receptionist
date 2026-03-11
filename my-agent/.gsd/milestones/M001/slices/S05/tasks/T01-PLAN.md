---
estimated_steps: 4
estimated_files: 4
---

# T01: Lock the S05 runtime boundary with failing gate, lifecycle, and entrypoint tests

**Slice:** S05 — Call Lifecycle Orchestration and After-Hours Gate
**Milestone:** M001

## Description

Create the RED proof boundary for S05 before implementation work lands. The tests must define the real operational contract: correct overnight gate behavior, durable transcript/finalization handling, caller-ID fallback semantics, failure-isolated CRM/SMS orchestration, and the actual `src/agent.py` runtime wiring.

## Steps

1. Add `tests/test_after_hours_gate.py` covering same-day and overnight time windows, midnight-crossing behavior in `America/Toronto`, injectable `now` handling, and the expected error path for invalid/missing timezone data.
2. Extend `tests/test_types.py` so the shared contracts fail honestly unless `BusinessConfig` exposes after-hours window fields and `CallIntakeRecord` exposes caller-ID plus callback-confirmation state.
3. Create `tests/test_call_lifecycle.py` with fake controller/session/service seams that assert transcript assembly order, complete vs partial finalization, caller-ID fallback when no confirmed callback number exists, finalize-once idempotence, independent CRM/SMS failure handling, and stable lifecycle diagnostics.
4. Update `tests/test_agent.py` to require S05 entrypoint composition: explicit dotenv loading for `.env.local` and `.env`, a call to the after-hours gate, lifecycle construction/subscription, and `session.generate_reply(...)` after `session.start(...)`, then run the named pytest command and confirm the failures are only from missing S05 implementation.

## Must-Haves

- [ ] The new tests import planned S05 modules directly (`orchestration.after_hours_gate`, `orchestration.call_lifecycle`, `classification.final_classifier`, `utils.time`, `utils.logging`) so missing runtime code fails honestly.
- [ ] At least one lifecycle test asserts the R009 fallback-phone rule explicitly: missing callback number falls back to caller ID and records that the number was not confirmed.
- [ ] At least one failure-path assertion checks stable diagnostic output (`snapshot()` and/or structured error metadata), not just free-form exception text.
- [ ] `tests/test_agent.py` proves real entrypoint wiring rather than only importability.

## Verification

- `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`
- Expected initial result: FAIL because the S05 modules/contracts/wiring are not implemented yet, while the tests themselves express the real slice boundary.

## Observability Impact

- Signals added/changed: Test-visible expectations for lifecycle phase/status fields, provider result metadata, and gate-decision diagnostics.
- How a future agent inspects this: Run the named pytest command and localize regressions by file (`test_after_hours_gate`, `test_call_lifecycle`, `test_agent`, or `test_types`).
- Failure state exposed: Incorrect gate math, missing caller-ID fallback, duplicate finalization, or opaque provider failures become targeted assertion failures instead of runtime guesswork.

## Inputs

- `src/agent.py` — current entrypoint that still lacks S05 gate/lifecycle/greeting wiring.
- `src/conversation/conversation_controller.py` — authoritative controller diagnostics the lifecycle must consume.
- `src/services/crm/crm_service.py` and `src/services/alerts/alert_service.py` — provider protocols the lifecycle must call independently.
- S05 research summary — establishes the need for session-event transcript capture, finalize-once behavior, caller-ID fallback, and a post-start greeting trigger.

## Expected Output

- `tests/test_after_hours_gate.py` — RED proof for timezone-safe overnight gate behavior.
- `tests/test_call_lifecycle.py` — RED proof for transcript assembly, finalization, provider isolation, and diagnostics.
- `tests/test_agent.py` — updated RED proof for real S05 entrypoint wiring.
- `tests/test_types.py` — updated RED contract assertions for the new config and call-record fields.
