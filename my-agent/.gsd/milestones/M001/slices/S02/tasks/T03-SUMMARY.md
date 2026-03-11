---
id: T03
parent: S02
milestone: M001
provides:
  - Stable LiveKit IntakeTask turn control with tool-driven slot updates, explicit tentative-slot confirmation, and guarded completion behavior
key_files:
  - src/conversation/intake_task.py
  - .gsd/milestones/M001/slices/S02/S02-PLAN.md
  - .gsd/STATE.md
key_decisions:
  - D018: IntakeTask now injects deterministic per-turn tool recommendations and reply requirements, including a same-turn no-self-confirm rule for tentative values
patterns_established:
  - Use prompt-time deterministic controller recommendations plus explicit reply requirements to stabilize LLM tool ordering and completion behavior in LiveKit evals
observability_surfaces:
  - `IntakeTask` guard summaries, predicted tool-action instructions, and the existing eval event stream/tool-call ordering in `tests/test_intake_task.py`
duration: 45m
verification_result: passed
completed_at: 2026-03-11 16:50 EDT
blocker_discovered: false
---

# T03: Implement LiveKit IntakeTask with tool-driven state updates and completion guards

**Hardened `src/conversation/intake_task.py` so the LiveKit intake evals consistently acknowledge captured details, keep tentative values unconfirmed until an explicit later turn, and complete only after required slots are confirmed.**

## What Happened

The existing `IntakeTask` implementation was close, but the LiveKit evals were still flaky in two important ways: on some runs the assistant reply omitted acknowledgement of the caller’s phone number and reported issue, and on other runs the model incorrectly self-confirmed same-turn tentative values and completed intake too early.

I reproduced the failures with the real eval suite, then tightened the task’s deterministic turn controller instead of changing test expectations. In `src/conversation/intake_task.py` I strengthened the runtime instructions so the model must:

- acknowledge every structured detail captured from the current turn,
- never use `confirm_slot` for a brand-new same-turn tentative value,
- never say intake is complete while required slots remain missing or tentative.

I also expanded the generated controller guidance so the model sees an explicit “do not confirm these same-turn tentative values yet” instruction and stronger per-turn reply requirements that enumerate the captured details to acknowledge.

Finally, I recorded the new stability decision in `.gsd/DECISIONS.md`, marked T03 complete in the slice plan, and advanced `.gsd/STATE.md` to T04.

## Verification

Ran fresh verification after the fix:

- `set -a && source .env.local && set +a && uv run pytest tests/test_intake_task.py -q` ✅
- Re-ran `set -a && source .env.local && set +a && uv run pytest tests/test_intake_task.py -q` a second time to check stability ✅
- `set -a && source .env.local && set +a && uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` ✅ (14 passed)
- `uv run ruff check src/ tests/` ✅

These checks confirm the T03 must-haves: slot mutations remain tool-driven, partial-volunteer and tentative-confirmation paths pass, and completion stays blocked until the policy-required slots are confirmed.

## Diagnostics

Future agents can inspect this work through:

- `tests/test_intake_task.py` event ordering, which exposes the exact function-tool boundary and completion timing
- `IntakeTask._build_instructions()` output, which now includes deterministic per-turn recommended actions and reply constraints
- `record_slot_candidate()`, `confirm_slot()`, and `complete_intake()` guard summaries, which expose missing/tentative state and whether completion is allowed

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/conversation/intake_task.py` — strengthened prompt-time controller rules and reply requirements to prevent same-turn tentative self-confirmation and improve acknowledgement consistency
- `.gsd/DECISIONS.md` — appended D018 documenting the stabilized IntakeTask turn-controller pattern
- `.gsd/milestones/M001/slices/S02/S02-PLAN.md` — marked T03 as complete
- `.gsd/STATE.md` — advanced the active task to T04 and recorded the new completion state
