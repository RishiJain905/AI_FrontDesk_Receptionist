# S01: Core Types, Config, and Data Model

**Goal:** Provide the fully typed, validated data contract used by all downstream features.
**Demo:** All types importable correctly and config load passes validation for demo profile without errors.

## Must-Haves

- `CallIntakeRecord` dataclass for CRM/SMS downstream use
- `BusinessConfig` dataclass for generic business setup
- `load_config()` validator that fails fast on missing required fields
- Enums for `SlotStatus`, `IssueCategory`, `UrgencyLevel`, `DangerType`

## Proof Level

- This slice proves: contract
- Real runtime required: no
- Human/UAT required: no

## Verification

- `uv run pytest tests/test_types.py`
- `uv run ruff check src/ tests/`

## Observability / Diagnostics

- Runtime signals: none (pure types slice)
- Inspection surfaces: none
- Failure visibility: validation errors raised instantly on boot in `load_config()` with descriptive messages
- Redaction constraints: none

## Integration Closure

- Upstream surfaces consumed: none
- New wiring introduced in this slice: none
- What remains before the milestone is truly usable end-to-end: Full LLM behavior, slot-filling logic, API integrations, and call lifecycle.

## Tasks

- [x] **T01: Enums and Slot State Types** `est:20m`
  - Why: Provides base vocabulary for conversation state and LLM classification.
  - Files: `src/hvac_types/__init__.py`, `src/hvac_types/classification.py`, `src/hvac_types/slot_state.py`, `tests/test_types.py`
  - Do: Create `hvac_types` package. Implement `IssueCategory`, `UrgencyLevel`, `DangerType` in `classification.py` and `SlotStatus`, `SlotState` in `slot_state.py`. Add tests asserting enum string values and default initialization. Use `from __future__ import annotations`.
  - Verify: `uv run pytest tests/test_types.py`
  - Done when: All enums are importable, string values match roadmap spec, and `SlotState` initializes cleanly.
- [x] **T02: Data Models for Configuration and Final Intake** `est:20m`
  - Why: Defines the data shape for passing config to the AI agent and the finalized record to the CRM.
  - Files: `src/hvac_types/business_config.py`, `src/hvac_types/call_intake_record.py`, `tests/test_types.py`
  - Do: Implement `BusinessConfig` with correct mutable list defaults (`field(default_factory=list)`). Implement `CallStatus` enum and `CallIntakeRecord` dataclass. Write tests checking default-factory safety (no shared lists between instances) and default missing states.
  - Verify: `uv run pytest tests/test_types.py`
  - Done when: Dataclasses instantiate without error, and tests prove list fields are not shared between instances.
- [x] **T03: Demo Config Profile and Runtime Validator** `est:20m`
  - Why: Provides the default config instance for the agent and ensures misconfigurations fail fast on boot.
  - Files: `src/config/__init__.py`, `src/config/hvac_demo_config.py`, `src/config/load_config.py`, `tests/test_types.py`
  - Do: Create `config` package. Define `HVAC_DEMO_CONFIG` singleton. Implement `load_config(config=None) -> BusinessConfig` checking for required fields (`business_name`, `timezone`, `owner_phone`). Add tests asserting validation passes for the demo config and raises `ValueError` otherwise.
  - Verify: `uv run pytest tests/test_types.py`
  - Done when: `load_config()` correctly raises `ValueError` on empty required fields and validates `HVAC_DEMO_CONFIG` successfully.
