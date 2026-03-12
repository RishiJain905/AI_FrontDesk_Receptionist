---
estimated_steps: 4
estimated_files: 4
---

# T04: Apply Ruff formatting to lifecycle utilities and re-verify diagnostics path

**Slice:** S06 — Full Test Suite and Demo Readiness
**Milestone:** M001

## Description

Finish formatter cleanup on the remaining source files and explicitly re-check lifecycle failure diagnostics to preserve S05 observability guarantees while closing S06 quality gates.

## Steps

1. Run Ruff formatter on `src/orchestration/after_hours_gate.py`, `src/orchestration/call_lifecycle.py`, and `src/utils/__init__.py`.
2. Review diffs to ensure lifecycle sequencing, provider-isolation behavior, and redaction logic are unchanged.
3. Run the targeted failure-path diagnostic test for lifecycle provider isolation and redaction.
4. Run full source-tree Ruff gates (`ruff check src/` and `ruff format --check src/`) and resolve any residual issues.

## Must-Haves

- [ ] Remaining unformatted source files are Ruff-format clean.
- [ ] Lifecycle failure-path diagnostics (`snapshot()` + redacted provider metadata) remain passing after formatting.
- [ ] Source-tree Ruff lint + format checks pass exactly as milestone DoD requires.

## Verification

- `uv run pytest tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider -q`
- `uv run ruff check src/ && uv run ruff format --check src/`

## Observability Impact

- Signals added/changed: None new; this task protects existing lifecycle diagnostic surfaces from regression.
- How a future agent inspects this: Run targeted lifecycle failure-path test and inspect `CallLifecycle.snapshot()` assertions.
- Failure state exposed: If formatting accidentally alters error redaction or provider-isolation behavior, the targeted lifecycle test fails with localized assertions.

## Inputs

- `src/orchestration/call_lifecycle.py` and `src/utils/logging.py` surfaces shipped in S05.
- T03 formatting pass output and current Ruff gate status.
- `tests/test_call_lifecycle.py` failure-path assertions.

## Expected Output

- `src/orchestration/after_hours_gate.py` — Ruff-formatted.
- `src/orchestration/call_lifecycle.py` — Ruff-formatted with behavior intact.
- `src/utils/__init__.py` — Ruff-formatted.
- `tests/test_call_lifecycle.py` — unchanged assertions still passing as observability guardrail.
