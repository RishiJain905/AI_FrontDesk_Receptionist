---
estimated_steps: 4
estimated_files: 3
---

# T02: Data Models for Configuration and Final Intake

**Slice:** S01 — Core Types, Config, and Data Model
**Milestone:** M001

## Description

Defines the core data structures passed to the AI agent (`BusinessConfig`) and the finalized record passed to the CRM (`CallIntakeRecord`). Focuses strongly on default factories for lists to avoid shared mutable state between configuration instances.

## Steps

1. Create `src/hvac_types/business_config.py` with `BusinessConfig` dataclass holding list fields like `safety_keywords` initialized with `field(default_factory=list)`. Use `from __future__ import annotations`.
2. Create `src/hvac_types/call_intake_record.py` with `CallStatus(str, Enum)` and `CallIntakeRecord` dataclass carrying optional strings and bools representing the finalized intake record.
3. Update `tests/test_types.py` with tests instantiating multiple `BusinessConfig` instances and asserting that appending to lists on one instance does not mutate the other.
4. Add tests asserting `CallIntakeRecord` defaults fields to `None` correctly.

## Must-Haves

- [ ] `BusinessConfig` dataclass implemented with mutable list defaults wrapped in `default_factory`.
- [ ] `CallIntakeRecord` dataclass for CRM/SMS downstream use representing a finalized record.
- [ ] `CallStatus(str, Enum)` with "partial" and "complete" statuses.

## Verification

- Run `uv run pytest tests/test_types.py`
- All tests should pass and confirm independent list instance allocation.

## Observability Impact

- Signals added/changed: None
- How a future agent inspects this: None
- Failure state exposed: None

## Inputs

- `src/hvac_types/classification.py` — Referenced implicitly by optional fields on the `CallIntakeRecord`.

## Expected Output

- `src/hvac_types/business_config.py` — Config data contract.
- `src/hvac_types/call_intake_record.py` — Finalized record data contract.
- `tests/test_types.py` — Tests validating independent list instances.
