---
estimated_steps: 5
estimated_files: 6
---

# T02: Implement deterministic slot tracker, intake policy, and live classifier core

**Slice:** S02 — Slot-Filling Intake and Background Classification
**Milestone:** M001

## Description

Build the framework-agnostic core that owns slot state, requirement policy, and lightweight transcript classification. This is the typed runtime boundary that S03/S05 will consume and the primary diagnostic surface for this slice.

## Steps

1. Create `src/conversation/__init__.py` and `src/classification/__init__.py` so the new S02 modules are package-safe and importable from tests and downstream slices.
2. Implement `src/conversation/slot_tracker.py` with deterministic slot registration, updates, semantic mapping from S01’s `EMPTY/FILLED/CONFIRMED` to missing/tentative/confirmed behavior, snapshot access, missing/tentative slot accessors, and required-slot confirmation checks.
3. Implement `src/conversation/intake_policy.py` with normal-mode required slots, danger-mode minimum-viable slots, and a hook that includes or excludes address capture based on classifier output or issue context.
4. Implement `src/classification/rules.py` and `src/classification/live_classifier.py` with rule-first keyword matching against config-driven safety/no-heat/no-cool vocabulary, typed `LiveClassification` output, and explicit fields for danger detection, urgency hint, issue category hint, and address relevance.
5. Run the unit suite, then refine naming or snapshot/output structure so tests can inspect failures directly without depending on model prose or hidden state.

## Must-Haves

- [ ] Tracker, policy, and classifier behavior is deterministic and directly inspectable from Python tests via typed return values/snapshots.
- [ ] Unit tests for slot semantics, required-slot selection, danger/urgency/category hints, and address relevance pass without depending on LiveKit runtime behavior.

## Verification

- `uv run pytest tests/test_slot_filling.py -q`
- `uv run ruff check src/conversation src/classification tests/test_slot_filling.py`

## Observability Impact

- Signals added/changed: Stable `SlotTracker` state snapshots and `LiveClassification` outputs become the canonical inspection surface for intake-state and live-classifier decisions.
- How a future agent inspects this: Import the tracker/classifier in tests or REPL and inspect snapshot fields / return values directly.
- Failure state exposed: Missing required slots, tentative slot residue, and classifier danger/urgency decisions become visible as structured state instead of prompt interpretation.

## Inputs

- `tests/test_slot_filling.py` — Failing proof target defining required tracker/policy/classifier interfaces and semantics.
- `src/hvac_types/slot_state.py`, `src/hvac_types/classification.py`, `src/config/hvac_demo_config.py` — S01 contracts and config-driven keyword seed data to build on without duplicating schema.

## Expected Output

- `src/conversation/slot_tracker.py` — Deterministic slot-state manager with inspection helpers.
- `src/conversation/intake_policy.py`, `src/classification/rules.py`, `src/classification/live_classifier.py` — Typed policy/classifier core passing the unit proof suite.
