---
id: M001
provides:
  - End-to-end HVAC after-hours voice intake runtime (adaptive slot-filling, safety handoff, lifecycle finalization, CRM/SMS integration boundaries, and release-readiness gates)
key_decisions:
  - D022/D023: safety handoff proof is function-tool-return driven and routed in llm_node for console/eval parity
  - D029/D030: provider boundaries enforce deterministic GHL matching and Twilio send/skip behavior behind protocol seams
  - D034/D036: after-hours gate is zoneinfo-first with deterministic fallback; entrypoint composes real providers when configured and no-op fallbacks otherwise
patterns_established:
  - Deterministic typed state surfaces for slot/classification/lifecycle diagnostics
  - Finalize-once orchestration with independent CRM/SMS failure isolation and redacted error metadata
  - Readiness artifacts (README/.env.example/pyproject) enforced by executable tests
observability_surfaces:
  - `CallLifecycle.snapshot()` and lifecycle phases (`finalize_started`, `crm_result`, `sms_result`, `finalize_completed`)
  - `tests/test_conversation_controller.py` handoff assertions (`agent_handoff`)
  - `uv run pytest`, `uv run ruff check src/ tests/`, `uv run ruff format --check src/`
requirement_outcomes: []
duration: ~16h10m aggregate across S01-S06
verification_result: blocked
completed_at: 2026-03-11
---

# M001: HVAC After-Hours Voice Agent

**Delivered a production-oriented HVAC after-hours agent stack with full automated test/readiness coverage, but milestone verification remains blocked on live credential-backed GHL/Twilio proof.**

## What Happened

M001 replaced the starter LiveKit assistant with a typed, config-driven HVAC intake system. S01 established the shared data/config contracts and fail-fast config validation. S02 added adaptive slot tracking, requirement policy, and deterministic live classification with guarded intake completion. S03 layered in real conversation control, deterministic prompts, and immediate safety handoff behavior. S04 implemented provider-backed GoHighLevel/Twilio services with deterministic payload builders and typed redacted errors. S05 wired after-hours gating, transcript assembly, final classification/summary, and finalize-once lifecycle orchestration into `src/agent.py`. S06 completed release readiness by enforcing docs/bootstrap contracts and rerunning full quality gates.

Together, these slices form a coherent runtime: greeting + adaptive intake + safety override + post-call finalization + CRM/SMS isolation, with test-enforced observability and reproducible bootstrap.

## Cross-Slice Verification

Success-criteria verification against M001 roadmap:

1. **Adaptive after-hours intake (name/phone/issue/callback, ask only missing info)** — **Met**
   - Evidence: `tests/test_slot_filling.py`, `tests/test_intake_task.py`, `tests/test_conversation_controller.py` (all passing in fresh `uv run pytest`: 131 passed).

2. **Immediate safety branch on danger signals with calm emergency guidance + minimum capture** — **Met**
   - Evidence: `tests/test_conversation_controller.py` asserts explicit `agent_handoff` + safety-first response behavior.

3. **Every complete/partial call persisted to GoHighLevel with transcript, summary, structured fields** — **Partially met (mock-proven, live proof missing)**
   - Evidence: `tests/test_call_lifecycle.py` + `tests/test_ghl_service.py` prove lifecycle invocation and deterministic payload/request shape via mock transport.
   - Gap: No fresh live credential-backed contact/note creation evidence captured in this completion unit.

4. **SMS sent only when `notifyOwner=true`** — **Met at automated boundary; live proof missing**
   - Evidence: `tests/test_sms_service.py` proves send/skip rules and duplicate-prevention behavior.
   - Gap: No fresh live Twilio delivery evidence captured in this completion unit.

5. **After-hours gate accurate across midnight (America/Toronto)** — **Met**
   - Evidence: `tests/test_after_hours_gate.py` passing in fresh full run.

6. **Major behavioral paths have passing pytest coverage** — **Met**
   - Fresh evidence: `uv run pytest` → `131 passed in 32.47s`.

Definition-of-done verification:

- All 6 slices `[x]` and all slice summaries present — **Met** (`S01..S06` summary files verified present).
- `src/agent.py` wired runtime behavior — **Met** via `tests/test_agent.py` + integration of controller/lifecycle tests.
- Safety branch trigger test — **Met**.
- Real GHL contact creation verification — **Not met in this unit**.
- Real SMS send verification — **Not met in this unit**.
- Midnight boundary gate tests — **Met**.
- `uv run pytest` — **Met (131 passed)**.
- `uv run ruff check src/` — **Met**.
- `uv run ruff format --check src/` — **Met**.

## Requirement Changes

- None. Requirement statuses remained unchanged (`active` / `deferred` / `out-of-scope`) during M001; this completion unit validated evidence, not status transitions.

## Forward Intelligence

### What the next milestone should know
- The strongest runtime truth source is lifecycle + controller typed diagnostics (`CallLifecycle.snapshot()`, handoff state, classification state), not prompt text.

### What's fragile
- Live provider proof remains outside deterministic CI: without credential-backed UAT artifacts, integration claims stay mock-verified only.

### Authoritative diagnostics
- Start with `uv run pytest` (full matrix) and then targeted seams: `tests/test_call_lifecycle.py` (orchestration/isolation) and `tests/test_conversation_controller.py` (safety handoff).

### What assumptions changed
- Assumption: full milestone closure could rely on deterministic local/CI gates alone.
- Actual: roadmap DoD still requires external live-provider evidence (GHL/Twilio) to mark verification as fully passed.

## Files Created/Modified

- `.gsd/milestones/M001/M001-SUMMARY.md` — milestone-level closure report with success-criteria and DoD verification outcomes.
- `.gsd/PROJECT.md` — updated to reflect milestone closure state and remaining live-UAT evidence gap.
- `.gsd/STATE.md` — updated active state for post-M001 follow-up posture.
