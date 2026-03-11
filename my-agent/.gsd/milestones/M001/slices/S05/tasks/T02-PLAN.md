---
estimated_steps: 5
estimated_files: 8
---

# T02: Extend the config and record contracts and implement the timezone-safe after-hours gate

**Slice:** S05 — Call Lifecycle Orchestration and After-Hours Gate
**Milestone:** M001

## Description

Build the pure shared boundary S05 depends on: config-driven after-hours fields, an explicit record model for caller-ID fallback, and timezone helpers/gate logic that can be trusted independently of the LiveKit runtime.

## Steps

1. Extend `src/hvac_types/business_config.py` with explicit after-hours window fields (for example `after_hours_start` / `after_hours_end`) while keeping the existing business identity/classification config intact.
2. Extend `src/config/hvac_demo_config.py` and `src/config/load_config.py` so the demo profile supplies the overnight defaults and config validation rejects blank or unparseable after-hours values before runtime boot.
3. Extend `src/hvac_types/call_intake_record.py` with explicit caller-ID and callback-confirmation fields so the lifecycle can represent the R009 fallback-phone path without burying it in notes.
4. Add `src/utils/time.py` with timezone-resolution and time-window parsing helpers that use `zoneinfo`, support injected datetimes for tests, and surface a clear error when timezone data is unavailable on Windows-like environments.
5. Add `src/orchestration/after_hours_gate.py` with pure gate helpers that correctly handle same-day and overnight windows, then run the gate/type tests until they pass.

## Must-Haves

- [ ] The after-hours window lives in `BusinessConfig`/demo config, not as a hardcoded `17:00–09:00` rule inside the gate logic.
- [ ] The gate accepts an injectable `now` so midnight-boundary cases are unit-testable without monkeypatching global time.
- [ ] Missing or invalid timezone data fails fast with a clear, actionable message instead of a vague `ZoneInfo` stack trace.
- [ ] `CallIntakeRecord` can now express both the raw caller ID and whether the callback number was explicitly confirmed.

## Verification

- `uv run pytest tests/test_after_hours_gate.py tests/test_types.py`
- Expected result: PASS, proving the pure config/time/gate boundary is correct before lifecycle orchestration depends on it.

## Observability Impact

- Signals added/changed: The gate becomes an inspectable pure boundary with deterministic inputs/outputs instead of hidden datetime math in the entrypoint.
- How a future agent inspects this: Run `tests/test_after_hours_gate.py` or import the time/gate helpers directly with an injected datetime.
- Failure state exposed: Bad hour parsing, wrong overnight logic, or missing timezone data now fail at a narrow boundary before the session boots.

## Inputs

- `tests/test_after_hours_gate.py` — RED gate expectations from T01.
- `tests/test_types.py` — RED config/record contract expectations from T01.
- `src/config/load_config.py` and `src/config/hvac_demo_config.py` — existing validated config seam to extend without undoing S01 behavior.
- Decision D005 — timezone handling remains on stdlib `zoneinfo` unless future evidence forces a change.

## Expected Output

- `src/hvac_types/business_config.py` — config-driven after-hours window fields.
- `src/hvac_types/call_intake_record.py` — explicit caller-ID/fallback-phone fields.
- `src/utils/time.py` — timezone-resolution and time-window helpers.
- `src/orchestration/after_hours_gate.py` — pure, testable after-hours gate logic.
