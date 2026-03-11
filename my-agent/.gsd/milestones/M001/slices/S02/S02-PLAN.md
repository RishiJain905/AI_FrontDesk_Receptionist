# S02: Slot-Filling Intake and Background Classification

**Goal:** Deliver the adaptive intake core for the HVAC after-hours agent: deterministic slot tracking and intake policy, lightweight live danger/urgency classification, and a LiveKit `IntakeTask` whose tool-driven multi-turn behavior proves required slots are collected adaptively and only completes when policy requirements are confirmed.
**Demo:** In tests, a caller can volunteer some details up front, the intake task records them via function tools, asks only for still-missing or tentative information, confirms low-confidence/tentative values before completion, and the live classifier flags danger and urgency signals early enough for S03 to branch on them.

## Must-Haves

- Adaptive slot state management exists with explicit missing/tentative/confirmed semantics mapped onto the shipped S01 slot contract, and required-slot completion checks depend on confirmed state rather than mere presence. (R002)
- Intake policy defines required slots for normal and danger-minimum-capture modes, with a clear hook for address relevance and downstream safety override behavior. (R002, R004)
- Live/background classification is implemented in code, not only prompts: danger, urgency, category hints, and address relevance are derived from transcript text using deterministic rules against config-driven keywords. (R004)
- A LiveKit `AgentTask` uses function tools to mutate intake state and completes only when all currently required slots are confirmed; multi-turn eval tests prove partial-volunteer and tentative-confirmation behavior. (R002, R004)
- Failure/inspection surfaces let a future agent inspect slot state, missing/tentative slots, and classification outputs without reading free-form prompt text. (diagnostics support for R002/R004)

## Proof Level

- This slice proves: contract and operational behavior at the slice boundary
- Real runtime required: no
- Human/UAT required: no

## Verification

- `tests/test_slot_filling.py` — unit tests for `SlotTracker` transitions, policy-required slot sets, and classifier rule outputs including danger, urgency, and address relevance.
- `tests/test_intake_task.py` — LiveKit `AgentSession` evals proving tool-driven multi-turn slot filling, no premature completion, and explicit confirmation of tentative slots before task completion.
- `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py`
- `uv run ruff check src/ tests/`

## Observability / Diagnostics

- Runtime signals: deterministic `SlotTracker.snapshot()` / slot-state accessors and structured `LiveClassification` outputs expose slot transitions and classifier decisions without depending on model prose.
- Inspection surfaces: unit tests can assert `get_missing_slots()`, `get_tentative_slots()`, `all_required_confirmed()`, and classifier return fields directly; intake task tests can inspect tool-call/completion behavior via `AgentSession` eval events.
- Failure visibility: incomplete required-slot state, tentative-slot residue, and danger/urgency reasoning surfaces remain inspectable as typed values instead of hidden prompt state.
- Redaction constraints: diagnostics must avoid logging raw caller PII beyond slot values already intentionally stored in memory for the call; no secrets from config or env are emitted.

## Integration Closure

- Upstream surfaces consumed: `src/hvac_types/slot_state.py`, `src/hvac_types/classification.py`, `src/hvac_types/business_config.py`, `src/hvac_types/call_intake_record.py`, `src/config/hvac_demo_config.py`, and LiveKit task/testing APIs already used by `tests/test_agent.py`.
- New wiring introduced in this slice: the `conversation` + `classification` runtime boundary and the first real `AgentTask` composition that S03 will embed into the HVAC intake agent.
- What remains before the milestone is truly usable end-to-end: S03 still must wire prompts, greeting flow, and safety handoff into the real agent; S04/S05 still must persist records, send alerts, and orchestrate post-call lifecycle.

## Tasks

- [x] **T01: Write failing slot-filling and intake-task proof tests** `est:50m`
  - Why: Verification must exist first so the slice proves adaptive behavior rather than stopping at scaffolding; these tests define the concrete acceptance boundary for R002/R004.
  - Files: `tests/test_slot_filling.py`, `tests/test_intake_task.py`
  - Do: Add unit tests for slot status mapping, tracker transitions, policy-required-slot selection, and live classifier outputs; add LiveKit eval tests for partial volunteer, tentative confirmation, and no-premature-completion behavior; keep imports pointed at the new S02 modules that do not exist yet so the tests fail initially for the right reason.
  - Verify: `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py`
  - Done when: The new tests exist with explicit assertions for the slice demo and they fail because the S02 modules/behavior are not implemented yet.
- [x] **T02: Implement deterministic slot tracker, intake policy, and live classifier core** `est:1h15m`
  - Why: These framework-agnostic state and classification primitives are the slice’s contract boundary and diagnostic surface; the intake task should build on them rather than reimplementing logic ad hoc.
  - Files: `src/conversation/__init__.py`, `src/conversation/slot_tracker.py`, `src/conversation/intake_policy.py`, `src/classification/__init__.py`, `src/classification/rules.py`, `src/classification/live_classifier.py`
  - Do: Create package-safe modules; normalize S01 `EMPTY/FILLED/CONFIRMED` into missing/tentative/confirmed semantics without mutating S01 contracts; implement required-slot selection for normal vs danger-minimum mode and address relevance hook; implement deterministic keyword-based classification using config-driven keywords and typed outputs/snapshots that tests can inspect directly.
  - Verify: `uv run pytest tests/test_slot_filling.py -q`
  - Done when: The slot/policy/classifier unit suite passes and exposes stable inspection helpers for missing/tentative slots and classifier decisions.
- [x] **T03: Implement LiveKit IntakeTask with tool-driven state updates and completion guards** `est:1h30m`
  - Why: This closes the loop from deterministic state into actual conversational task behavior, proving the roadmap’s tool-driven slot-filling strategy works in multi-turn evals.
  - Files: `src/conversation/intake_task.py`, `src/conversation/__init__.py`, `tests/test_intake_task.py`
  - Do: Implement `IntakeTask(AgentTask)` using well-documented function tools for recording slot candidates, confirming/rejecting tentative values, and exposing completion only when policy-required slots are confirmed; wire it to the tracker/classifier primitives and keep completion idempotency constraints explicit so tests can prove no early or double completion behavior.
  - Verify: `uv run pytest tests/test_intake_task.py -q`
  - Done when: The intake task passes multi-turn eval tests showing adaptive slot filling, tentative confirmation before completion, and completion only after all required slots are confirmed.
- [x] **T04: Run slice verification, tighten diagnostics, and document the planning handoff surfaces** `est:35m`
  - Why: The slice needs an honest closeout boundary with green verification and explicit diagnostic surfaces future slices can rely on.
  - Files: `src/conversation/slot_tracker.py`, `src/classification/live_classifier.py`, `src/conversation/intake_task.py`, `tests/test_slot_filling.py`, `tests/test_intake_task.py`
  - Do: Run the full slice verification commands; make any small naming/diagnostic refinements needed for test clarity; ensure slot snapshots and classifier outputs stay stable and inspectable; leave modules in a shape S03 can import directly without hidden TODO behavior.
  - Verify: `uv run pytest tests/test_slot_filling.py tests/test_intake_task.py && uv run ruff check src/ tests/`
  - Done when: All slice verification commands pass and the diagnostics described above are exercised by at least one assertion in the test suite.

## Files Likely Touched

- `src/conversation/__init__.py`
- `src/conversation/slot_tracker.py`
- `src/conversation/intake_policy.py`
- `src/conversation/intake_task.py`
- `src/classification/__init__.py`
- `src/classification/rules.py`
- `src/classification/live_classifier.py`
- `tests/test_slot_filling.py`
- `tests/test_intake_task.py`
