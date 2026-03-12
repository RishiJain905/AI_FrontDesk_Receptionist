---
estimated_steps: 4
estimated_files: 6
---

# T03: Apply Ruff formatting to agent/controller/classification surfaces

**Slice:** S06 — Full Test Suite and Demo Readiness
**Milestone:** M001

## Description

Normalize formatting on the first batch of unformatted source files in agent/conversation/classification paths so S06 can close the formatter gate without introducing behavioral churn.

## Steps

1. Run Ruff formatter on the known unformatted runtime files: `src/agent.py`, `src/classification/rules.py`, `src/conversation/__init__.py`, `src/conversation/conversation_controller.py`, `src/conversation/intake_task.py`, and `src/conversation/prompts.py`.
2. Review formatter diffs for import ordering and line wrapping changes that could affect readability; avoid logic edits outside style normalization.
3. Run targeted behavior tests for controller/intake/entrypoint seams to confirm no regressions from formatting-only edits.
4. Re-run file-scoped `ruff format --check` on the same list and fix any remaining style drift.

## Must-Haves

- [ ] All listed files are format-clean under Ruff without functional behavior changes.
- [ ] Conversation controller/intake and entrypoint-related tests remain green after formatting.
- [ ] No prompt or runtime policy semantics are changed in this formatting pass.

## Verification

- `uv run pytest tests/test_conversation_controller.py tests/test_intake_task.py tests/test_agent.py -q`
- `uv run ruff format --check src/agent.py src/classification/rules.py src/conversation/__init__.py src/conversation/conversation_controller.py src/conversation/intake_task.py src/conversation/prompts.py`

## Observability Impact

- Signals added/changed: None (format-only task).
- How a future agent inspects this: Compare Git diff for style-only changes and run targeted tests listed above.
- Failure state exposed: Any accidental behavior change surfaces in conversation/controller/entrypoint tests before full-suite execution.

## Inputs

- `pyproject.toml` — tool configuration added in T02.
- `src/agent.py` and conversation/classification modules — current runtime behavior to preserve.
- Current Ruff formatter output listing these files as unformatted.

## Expected Output

- `src/agent.py` — Ruff-formatted, behavior-preserving.
- `src/classification/rules.py` — Ruff-formatted.
- `src/conversation/__init__.py` — Ruff-formatted.
- `src/conversation/conversation_controller.py` — Ruff-formatted.
- `src/conversation/intake_task.py` — Ruff-formatted.
- `src/conversation/prompts.py` — Ruff-formatted.
