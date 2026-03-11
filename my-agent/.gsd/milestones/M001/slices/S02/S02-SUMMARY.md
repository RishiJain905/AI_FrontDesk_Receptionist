---
id: S02
parent: M001
milestone: M001
provides:
  - Deterministic slot tracking, intake policy, live transcript classification, and a guarded LiveKit IntakeTask proof boundary for adaptive HVAC intake
requires:
  - slice: S01
    provides: Core config and HVAC type contracts (`BusinessConfig`, `CallIntakeRecord`, `SlotState`, `SlotStatus`, and classification enums)
affects:
  - S03
  - S05
key_files:
  - src/conversation/slot_tracker.py
  - src/conversation/intake_policy.py
  - src/classification/live_classifier.py
  - src/classification/rules.py
  - src/conversation/intake_task.py
  - tests/test_slot_filling.py
  - tests/test_intake_task.py
  - tests/conftest.py
key_decisions:
  - D016: Keep S02 proof tests importing planned `conversation.*` and `classification.*` modules directly so RED state fails on the real runtime boundary
  - D017: Preserve S01 `SlotStatus.EMPTY/FILLED/CONFIRMED` as storage and expose S02 missing/tentative/confirmed semantics through `SlotTracker`
  - D018: Inject deterministic per-turn tool recommendations and reply requirements into `IntakeTask`, including a no same-turn self-confirm rule for tentative values
  - D019: Load `.env.local` first and then `.env` in pytest so the named slice verification command works with securely collected local LiveKit credentials
patterns_established:
  - Keep rule-first classification and required-slot policy outside prompt prose so downstream agents can inspect typed state directly
  - Stabilize LiveKit eval behavior by combining deterministic controller recommendations with tool-only state mutation and guarded completion
observability_surfaces:
  - `SlotTracker.snapshot()`, `get_missing_slots()`, `get_tentative_slots()`, and `all_required_confirmed()`
  - `LiveClassification` fields (`danger_type`, `urgency_level`, `issue_category`, `address_relevant`, `matched_keywords`)
  - `tests/test_intake_task.py` function-call ordering and completion timing via `AgentSession` eval events
  - `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py`
  - `uv run ruff check src/ tests/`
drill_down_paths:
  - .gsd/milestones/M001/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T03-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T04-SUMMARY.md
duration: 2h50m
verification_result: passed
completed_at: 2026-03-11 17:34 EDT
---

# S02: Slot-Filling Intake and Background Classification

**Shipped the adaptive intake core: deterministic slot-state tracking, config-driven live classification, and a LiveKit `IntakeTask` that only completes after required slots are truly confirmed.**

## What Happened

S02 started by locking the boundary in tests instead of scaffolding. `tests/test_slot_filling.py` defined the expected semantics for missing/tentative/confirmed slot handling, required-slot policy selection, and deterministic transcript classification. `tests/test_intake_task.py` defined the live proof boundary for multi-turn tool-driven intake behavior: callers can volunteer partial information up front, tentative values must be explicitly confirmed later, and intake must not complete early.

With that RED boundary in place, the slice implemented the reusable state and classification core. `src/conversation/slot_tracker.py` preserves the S01 `SlotState` storage contract while exposing S02 inspection helpers that future slices can use directly. `src/conversation/intake_policy.py` separates requirement policy from mutable state, making normal-mode and danger-minimum capture explicit. `src/classification/rules.py` and `src/classification/live_classifier.py` moved danger, urgency, category, and address-relevance logic into deterministic code driven by business config keywords rather than prompt wording.

The slice then closed the loop with `src/conversation/intake_task.py`. The task uses function tools for slot mutation, recomputes live classification as transcript accumulates, injects deterministic per-turn action recommendations, and blocks `complete_intake()` until the policy-required slots are confirmed. The task also prevents same-turn self-confirmation for tentative values, which stabilized the LiveKit eval behavior around explicit later-turn confirmation.

During closeout, slice verification exposed one operational gap: the named pytest command could not construct LiveKit inference models unless dotenv files were loaded for tests. `tests/conftest.py` fixed that by loading `.env.local` first and then `.env`, keeping the verification command honest without shell-specific setup. The final result is a green, inspectable S02 boundary that S03 can embed directly into the conversation controller and safety handoff.

## Verification

Fresh slice-level verification was run at completion:

- `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` ✅ `14 passed`
- `uv run ruff check src/ tests/` ✅ `All checks passed!`

Those checks exercise the promised diagnostics directly:

- slot snapshots, missing/tentative accessors, and required-slot completion checks in `tests/test_slot_filling.py`
- typed classifier outputs for danger, urgency, issue category, and address relevance in `tests/test_slot_filling.py`
- function-tool ordering, no-premature-completion behavior, and tentative confirmation before completion in `tests/test_intake_task.py`
- test-time env loading via `tests/conftest.py`, which makes the named verification command reproducible locally

## Requirements Advanced

- R002 — Added deterministic slot tracking, required-slot policy, and tool-driven multi-turn intake behavior that asks only for missing information and confirms tentative values before completion.
- R004 — Added rule-based live classification for danger, urgency, issue category, and address relevance, and wired that classification into the intake runtime boundary.

## Requirements Validated

- R002 — `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` now proves missing/tentative/confirmed semantics, adaptive partial-volunteer intake, explicit confirmation of tentative values, and completion guards based on confirmed required slots.
- R004 — `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py` now proves deterministic live danger/urgency/category/address-relevance classification and its inspectable typed outputs.

## New Requirements Surfaced

- none.

## Requirements Invalidated or Re-scoped

- none.

## Deviations

Added `tests/conftest.py` even though it was not called out in the slice task list. This was necessary to make the exact named verification command runnable with securely collected local LiveKit credentials, without undocumented shell export steps.

## Known Limitations

- S02 stops at the intake-task boundary. It does not yet provide the full HVAC agent greeting, safety handoff, closing behavior, CRM persistence, SMS alerts, or after-hours orchestration.
- Danger detection is now available as structured live classification, but S03 still must use it to interrupt normal intake and switch to safety-first conversation behavior.
- The LiveKit eval proof depends on local inference credentials being present through `.env.local` or `.env`.

## Follow-ups

- S03 should wire `IntakeTask`, `LiveClassifier`, and the new policy surfaces into `HVACIntakeAgent` and `SafetyAgent`, with evals that prove immediate safety handoff on danger keywords.
- S05 should consume the same typed slot/classification surfaces when building incremental `CallIntakeRecord` updates and finalization logic.

## Files Created/Modified

- `src/conversation/__init__.py` — exports the S02 conversation primitives for downstream imports.
- `src/conversation/slot_tracker.py` — implements deterministic slot registration, candidate recording, confirmation, rejection, snapshots, and required-slot inspection helpers.
- `src/conversation/intake_policy.py` — defines normal vs danger-minimum required-slot policy and address-collection logic.
- `src/conversation/intake_task.py` — implements the guarded LiveKit intake task with function tools, per-turn controller recommendations, and completion gating.
- `src/classification/__init__.py` — exports the S02 classification primitives.
- `src/classification/rules.py` — implements deterministic keyword matching and classification helper rules.
- `src/classification/live_classifier.py` — exposes typed, inspectable live classification results from config-driven keywords.
- `tests/test_slot_filling.py` — proves slot tracker semantics, intake policy selection, and deterministic classifier outputs.
- `tests/test_intake_task.py` — proves tool-call ordering, adaptive slot filling, tentative confirmation, and guarded completion in LiveKit evals.
- `tests/conftest.py` — loads `.env.local` and `.env` for pytest so the named LiveKit eval command runs without shell-specific setup.

## Forward Intelligence

### What the next slice should know
- `IntakeTask` is already the authoritative structured intake boundary. S03 should wrap it rather than reimplement slot logic in agent prompts or event handlers.
- `LiveClassification.address_relevant` and `get_required_slots()` are the intended hooks for deciding whether address capture is required in a given path.
- The classifier is intentionally deterministic and lightweight; if S03 needs safety branching, it should trust these typed outputs instead of asking the model to infer danger only from prompt text.

### What's fragile
- `src/conversation/intake_task.py` — the eval stability currently relies on prompt-time deterministic controller recommendations and the no-same-turn-self-confirm rule; weakening those instructions may reintroduce flaky tool ordering or early completion.
- Local test execution — LiveKit inference-backed evals still require local credentials through `.env.local` or `.env`; missing env will fail early during fixture construction.

### Authoritative diagnostics
- `tests/test_intake_task.py` — best proof of whether intake completion ordering and tentative confirmation still work, because it asserts actual function-call events instead of only reading model prose.
- `tests/test_slot_filling.py` — fastest proof for slot semantics and live classification regressions because it asserts the typed surfaces directly.
- `SlotTracker.snapshot()` and `LiveClassification` — most trustworthy runtime inspection surfaces because they expose structured state outside prompt text.

### What assumptions changed
- "Pytest will inherit the same env setup as local console runs" — false; tests needed their own dotenv loading path in `tests/conftest.py`.
- "Prompt instructions alone will keep tentative values from being over-confirmed" — not reliably enough; explicit per-turn controller recommendations and the same-turn confirmation guard were needed to stabilize the evals.
