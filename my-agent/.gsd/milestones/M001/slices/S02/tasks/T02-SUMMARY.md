---
id: T02
parent: S02
milestone: M001
provides:
  - Deterministic slot-tracking, intake-policy, and live-classifier primitives for S02 unit tests and downstream intake-task work
key_files:
  - src/conversation/slot_tracker.py
  - src/conversation/intake_policy.py
  - src/classification/live_classifier.py
  - src/classification/rules.py
key_decisions:
  - D017: Preserve S01 SlotStatus storage semantics and layer S02 missing/tentative inspection helpers in SlotTracker
patterns_established:
  - Rule-first transcript classification returns typed, directly inspectable outputs instead of prompt-derived prose
  - Required-slot policy stays separate from tracker state so later tasks can swap NORMAL vs DANGER_MINIMUM capture cleanly
observability_surfaces:
  - SlotTracker.snapshot(), get_missing_slots(), get_tentative_slots(), all_required_confirmed(), and LiveClassification fields
duration: 55m
verification_result: passed
completed_at: 2026-03-11
blocker_discovered: false
---

# T02: Implement deterministic slot tracker, intake policy, and live classifier core

**Added the S02 package-safe runtime core for slot state, required-slot policy, and deterministic live transcript classification.**

## What Happened

Created `src/conversation/__init__.py` and `src/classification/__init__.py` so the new S02 modules import cleanly from tests and downstream slices.

Implemented `src/conversation/slot_tracker.py` as the stable slot-state boundary over the shipped S01 `SlotState` contract. The tracker now supports deterministic registration, candidate recording, confirmation, rejection, detached snapshots, explicit missing-slot inspection, tentative-slot inspection, and required-slot confirmation checks.

Implemented `src/conversation/intake_policy.py` with `IntakeMode.NORMAL` and `IntakeMode.DANGER_MINIMUM`, plus a `should_collect_address()` hook and `get_required_slots()` helper so address capture can be included or skipped without hiding the policy logic inside conversation code.

Implemented `src/classification/rules.py` and `src/classification/live_classifier.py` as a rule-first, config-seeded classifier. The live classifier returns a typed `LiveClassification` object with `danger_type`, `urgency_level`, `issue_category`, `address_relevant`, `matched_keywords`, and a derived `danger_detected` property. During verification, one classifier test initially failed because generic smell matching incorrectly downgraded gas-smell danger into `BAD_SMELL`; the fix was to preserve the danger classification and normalize that case back to `IssueCategory.OTHER`.

Appended decisions D016 and D017 to `.gsd/DECISIONS.md`, marked T02 complete in the slice plan, and advanced `.gsd/STATE.md` to T03.

## Verification

Task-level verification passed:

- `uv run pytest tests/test_slot_filling.py -q` ✅ — 11 passed
- `uv run ruff check src/conversation src/classification tests/test_slot_filling.py` ✅

Slice-level verification run for honest status:

- `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` ⚠️ — `tests/test_slot_filling.py` passed, but collection stops because `conversation.intake_task` is still intentionally unimplemented for T03
- `uv run ruff check src/ tests/` ✅

## Diagnostics

Future agents can inspect the shipped behavior directly through:

- `SlotTracker.snapshot()` for detached per-slot `SlotState` values
- `SlotTracker.get_missing_slots()` for required-but-empty slots
- `SlotTracker.get_tentative_slots()` for unconfirmed candidates
- `SlotTracker.all_required_confirmed()` for completion gating
- `LiveClassifier.classify(...)` returning a typed `LiveClassification` object with stable fields and matched keyword evidence

## Deviations

None.

## Known Issues

- `tests/test_intake_task.py` still fails at import/collection because `src/conversation/intake_task.py` is not part of T02 and remains for T03.

## Files Created/Modified

- `src/conversation/__init__.py` — package exports for conversation-state primitives
- `src/conversation/slot_tracker.py` — deterministic slot-state manager with snapshot and inspection helpers
- `src/conversation/intake_policy.py` — normal vs danger-minimum required-slot policy and address hook
- `src/classification/__init__.py` — package exports for live classification primitives
- `src/classification/rules.py` — transcript normalization and deterministic keyword-rule helpers
- `src/classification/live_classifier.py` — typed live classifier implementation over config-driven keywords
- `.gsd/DECISIONS.md` — appended D016/D017 for S02 proof-boundary and slot-semantics normalization decisions
- `.gsd/milestones/M001/slices/S02/S02-PLAN.md` — marked T02 complete
- `.gsd/STATE.md` — advanced active task to T03
