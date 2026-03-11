# S05: Call Lifecycle Orchestration and After-Hours Gate — UAT

**Milestone:** M001
**Written:** 2026-03-11

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S05’s slice plan explicitly targets operational proof via deterministic runtime seams/tests (not live telephony), and all required gate/lifecycle/entrypoint behaviors are covered by executable pytest assertions.

## Preconditions

- Repository is on the S05 branch state.
- Python/uv environment is available.
- Test dependencies are installed.

## Smoke Test

Run:

- `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`

Expected: all tests pass, confirming S05 core orchestration surfaces are wired and behaving correctly.

## Test Cases

### 1. After-hours gate boundary and wiring

1. Run `uv run pytest tests/test_after_hours_gate.py tests/test_agent.py tests/test_types.py`
2. Review passing assertions for overnight boundary behavior (`17:00` → `09:00`), timezone safety, config validation, and entrypoint gate invocation.
3. **Expected:** gate decisions are correct across midnight and entrypoint includes gate + dotenv + greeting composition.

### 2. Call lifecycle finalize behavior and provider isolation

1. Run `uv run pytest tests/test_call_lifecycle.py tests/test_agent.py`
2. Review passing assertions for complete vs partial finalization, caller-ID fallback semantics, finalize-once idempotence, and CRM/SMS independent failure handling.
3. **Expected:** lifecycle finalizes once, preserves partial-call records, and exposes actionable diagnostics without cross-provider blocking.

## Edge Cases

### Missing callback number on partial call

1. Run `uv run pytest tests/test_call_lifecycle.py -k fallback`
2. **Expected:** finalized record uses `caller_id` as fallback phone and sets `callback_number_confirmed=False`.

## Failure Signals

- Any failure in `tests/test_after_hours_gate.py` indicates incorrect timezone/window math or invalid gate contract behavior.
- Any failure in `tests/test_call_lifecycle.py` indicates finalize-once, partial-call handling, transcript assembly, or provider isolation regressions.
- Any failure in `tests/test_agent.py` indicates broken runtime composition (dotenv load, gate invocation, lifecycle attachment, greeting trigger).

## Requirements Proved By This UAT

- **R007** — after-hours gate correctness and entrypoint gate wiring are proven by gate/type/agent tests.
- **R009** — graceful partial finalization, caller-ID fallback, finalize idempotence, and CRM/SMS isolation are proven by lifecycle/agent tests.
- **R005 (supporting)** — lifecycle orchestration proves CRM invocation from finalized records under complete/partial paths (service-level payload correctness remains covered by S04 tests).

## Not Proven By This UAT

- Live GoHighLevel API write success with real credentials.
- Live Twilio SMS delivery success with real credentials.
- Human voice/SIP conversational quality and operational runbook readiness.

## Notes for Tester

- This UAT is intentionally artifact-driven for S05. Live-provider and live-call verification are deferred to S06/demo closure.
- If a failure appears, start with the corresponding focused test file before running the full milestone suite.
