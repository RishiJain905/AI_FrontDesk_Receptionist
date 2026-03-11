# S02: Slot-Filling Intake and Background Classification — UAT

**Milestone:** M001
**Written:** 2026-03-11

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S02 proves an internal runtime boundary, not a human-facing end-to-end call flow. The strongest acceptance evidence for this slice is the automated LiveKit eval/test artifact set that exercises slot tracking, classification, and guarded intake completion directly.

## Preconditions

- Project dependencies are installed via `uv`.
- LiveKit inference credentials are available in `.env.local` or `.env` so the eval fixture can construct `inference.LLM(...)`.
- Run from the project root: `F:\Personal\AI Agents\AI_FrontDesk_Receptionist\my-agent`.

## Smoke Test

Run:

- `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py`

Passing output (`14 passed`) confirms the slice boundary is basically working.

## Test Cases

### 1. Partial volunteer intake asks only for remaining required slots

1. Run `uv run pytest tests/test_intake_task.py -q`.
2. Observe the `test_partial_volunteer_flow_only_asks_for_remaining_required_slots` eval.
3. **Expected:** The task records the volunteered name, phone number, and issue category through function tools, acknowledges them, and asks only for the missing service address.

### 2. Tentative values require explicit later confirmation

1. Run `uv run pytest tests/test_intake_task.py -q`.
2. Observe the `test_tentative_slot_requires_explicit_confirmation_before_completion` eval.
3. **Expected:** The first turn stores tentative name/address values without completing intake; the second turn confirms them, then and only then triggers `complete_intake`.

### 3. Deterministic classifier exposes inspectable danger and urgency output

1. Run `uv run pytest tests/test_slot_filling.py -q`.
2. Observe the classifier tests for gas smell/CO, no heat with vulnerable occupant, callback-only request, and flooding.
3. **Expected:** `LiveClassification` returns the expected `danger_type`, `urgency_level`, `issue_category`, `address_relevant`, and matched keyword evidence for each transcript.

## Edge Cases

### Completion blocked while a required slot is still missing

1. Run `uv run pytest tests/test_intake_task.py -q`.
2. Observe `test_completion_is_blocked_until_all_required_slots_are_confirmed`.
3. **Expected:** Intake does not complete after the caller gives only name + issue, still does not complete after phone number alone, and completes only after the required address is captured.

### Address can be skipped when classification says it is not relevant

1. Run `uv run pytest tests/test_slot_filling.py -q`.
2. Observe `test_normal_mode_can_skip_address_when_classifier_marks_it_not_relevant`.
3. **Expected:** `get_required_slots(mode=IntakeMode.NORMAL, address_relevant=False)` omits `service_address` from the required set.

## Failure Signals

- `ModuleNotFoundError` for `conversation.*` or `classification.*` indicates the slice boundary is missing or broken.
- A failing `test_intake_task.py` assertion on function-call ordering indicates the task is no longer reliably tool-driven.
- A failing `test_slot_filling.py` classifier assertion indicates danger/urgency/category/address logic drifted away from the typed contract.
- Fixture failure about missing `LIVEKIT_API_KEY` or similar indicates local test env loading is broken or secrets are absent.

## Requirements Proved By This UAT

- R002 — Proves adaptive slot-filling with missing/tentative/confirmed semantics, explicit later confirmation of tentative values, and no premature completion.
- R004 — Proves deterministic live danger/urgency/category/address-relevance classification is implemented in code and exposed through typed outputs.

## Not Proven By This UAT

- R001 — Does not prove the full after-hours conversational flow, opening greeting, callback-time collection, or complete `CallIntakeRecord` orchestration.
- R003 — Does not prove live safety handoff behavior; S03 must show the agent actually switches into a safety-first branch.
- R005 / R006 / R007 / R009 / R010 — Does not prove CRM writes, SMS sending, after-hours gating, graceful hangup handling, or full-suite milestone coverage.
- Human call quality, voice tone, and live telephony behavior are intentionally not covered by this slice UAT.

## Notes for Tester

This slice is intentionally best verified through test artifacts rather than a human voice demo. If the proof suite is green but a downstream slice later fails, start with `tests/test_slot_filling.py` for typed state/classification regressions and `tests/test_intake_task.py` for tool-ordering/completion regressions.
