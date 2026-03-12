# S06: Full Test Suite and Demo Readiness — UAT

**Milestone:** M001
**Written:** 2026-03-11

## UAT Type

- UAT mode: mixed (artifact-driven + human-experience)
- Why this mode is sufficient: S06 primarily proves release-readiness contracts and reproducible quality gates, but milestone acceptance still needs a human-run console demo with live provider credentials for operational confidence.

## Preconditions

- Repo cloned and dependencies installed via `uv sync --dev`.
- `.env` created from `.env.example` with real (or test) credentials for LiveKit, GoHighLevel, and Twilio.
- Tester has access to verify resulting GoHighLevel contact/note and owner SMS delivery.

## Smoke Test

Run the readiness gate exactly:

1. `uv run pytest tests/test_s06_readiness.py tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider`
2. `uv run pytest`
3. `uv run ruff check src/`
4. `uv run ruff format --check src/`

**Expected:** all commands pass; readiness artifacts and lifecycle diagnostics contracts are intact.

## Test Cases

### 1. Clean bootstrap + full quality gate

1. From clean clone: run `uv sync --dev`.
2. Run `uv run pytest`.
3. Run Ruff gates (`uv run ruff check src/`, `uv run ruff format --check src/`).
4. **Expected:** bootstrap succeeds and full test/lint/format gates pass with no failures.

### 2. Console demo — normal intake path

1. Start agent in console mode: `uv run python src/agent.py console`.
2. Simulate a normal after-hours no-heat caller and provide name, callback number, issue summary, callback time.
3. End call normally.
4. **Expected:** intake completes naturally, call finalizes once, CRM record/note appears, SMS behavior matches `notifyOwner` classification.

### 3. Console demo — safety escalation path

1. Start console mode again.
2. Include danger language (e.g., gas smell / burning smell) early in the call.
3. Complete minimal intake and end the call.
4. **Expected:** immediate safety-first guidance/handoff behavior, `dangerDetected` semantics reflected in final record, owner SMS escalation triggered.

## Edge Cases

### Partial hang-up path

1. Start console mode and provide incomplete intake details.
2. End/hang up before all required slots are confirmed.
3. **Expected:** lifecycle finalizes as partial, caller-id fallback is used when callback number is unconfirmed/missing, and CRM write still occurs.

## Failure Signals

- `uv sync --dev` cannot resolve/install project dependencies.
- Any failure in `tests/test_s06_readiness.py` (docs/bootstrap contract drift).
- Any failure in lifecycle provider isolation diagnostics test (`test_lifecycle_records_structured_provider_failures_without_blocking_other_provider`).
- Missing/incorrect CRM note fields after demo calls.
- SMS sent when `notifyOwner=false` or not sent when escalation path clearly requires it.
- Secret/token values visible in logs/snapshots or shared artifacts.

## Requirements Proved By This UAT

- **R010** — Readiness-contract tests + full-suite + Ruff gates provide repeatable test-coverage closure evidence.
- **R009 (operational slice of observability/failure isolation)** — lifecycle failure-path test confirms structured/redacted provider diagnostics with isolated CRM/SMS outcomes.

## Not Proven By This UAT

- End-to-end telephony quality under real SIP/PSTN load (latency/audio/network variability).
- Long-running production reliability, retries, or provider outage recovery beyond deterministic test seams.
- Deferred scope items (R020 email, R021 multilingual, R022 scheduling).

## Notes for Tester

Use README demo prompts to keep coverage consistent (normal intake, safety escalation, partial call). Capture screenshots/logs with secrets redacted; never paste live tokens into tracked files or issue comments.
