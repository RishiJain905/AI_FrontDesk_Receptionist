# GSD State

**Active Milestone:** M001 — HVAC After-Hours Voice Agent
**Active Slice:** None (S01–S06 complete)
**Active Task:** None
**Phase:** S06 closure complete and committed; milestone implementation is complete with deterministic readiness gates passing.

## Recent Decisions

- D037: S06 starts with a dedicated RED readiness test boundary for `README.md`, `.env.example`, and `pyproject.toml`.
- D038: S06 closure requires fresh execution of `uv sync --dev`, full pytest, and source Ruff lint/format gates, plus updated R010 traceability.
- D039: Readiness tests enforce README command evidence, provider env-key coverage with placeholder-only values, and pyproject metadata/tool contracts.
- D040: Bootstrap manifest baseline uses setuptools `src/` discovery + explicit runtime deps + uv `dependency-groups.dev` for deterministic `uv sync --dev`.
- D041: Intake confirmation eval assertions accept either equivalent confirmation tool path (`confirm_slot` or `record_slot_candidate`) to remove LLM tool-selection flake while preserving completion guarantees.

## Blockers

- None.

## Next Action

Execute and archive live credential-backed UAT evidence (real GoHighLevel + Twilio outcomes) using `.gsd/milestones/M001/slices/S06/S06-UAT.md` and README demo flow.
