---
estimated_steps: 4
estimated_files: 4
---

# T01: Enums and Slot State Types

**Slice:** S01 — Core Types, Config, and Data Model
**Milestone:** M001

## Description

Provides the base vocabulary for conversation state and LLM classification. This includes issue categories, urgency levels, danger types, and slot statuses. These types form the fundamental contract for downstream intent classification.

## Steps

1. Create `src/hvac_types/` directory and an empty `__init__.py`.
2. Write `tests/test_types.py` asserting that the enums are importable, their string representations match expectations, and `SlotState` initializes cleanly. (This should fail initially).
3. Create `src/hvac_types/classification.py` implementing `IssueCategory`, `UrgencyLevel`, and `DangerType` as subclasses of `str, Enum`. Include `from __future__ import annotations`.
4. Create `src/hvac_types/slot_state.py` implementing `SlotStatus(str, Enum)` and `SlotState` dataclass.

## Must-Haves

- [ ] `IssueCategory`, `UrgencyLevel`, `DangerType` implemented as `str, Enum`
- [ ] `SlotStatus` and `SlotState` implemented correctly
- [ ] Tests verifying initialization and string enum values

## Verification

- Run `uv run pytest tests/test_types.py`
- All tests should pass.

## Observability Impact

- Signals added/changed: None
- How a future agent inspects this: None
- Failure state exposed: None

## Inputs

- None — This is the first foundational task.

## Expected Output

- `src/hvac_types/classification.py` — Enums for classification intents.
- `src/hvac_types/slot_state.py` — Enums and Dataclasses for slot management.
- `tests/test_types.py` — Verifying the structure and initialization behavior of types.
