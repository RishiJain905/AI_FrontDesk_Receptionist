---
estimated_steps: 4
estimated_files: 3
---

# T03: Rewire the entrypoint to the HVAC controller and prove console-path composition

**Slice:** S03 — Conversation Controller, Prompts, and Safety Branch
**Milestone:** M001

## Description

Finish S03 by replacing the scaffold assistant in the runnable entrypoint with the HVAC conversation controller while preserving the current LiveKit server/session setup. This closes the real composition loop for console mode and prevents S03 from being only a library-level implementation.

## Steps

1. Update `src/agent.py` to load config and start the session with the S03 HVAC controller instead of the generic starter `Assistant`, while keeping the existing `AgentServer`, `prewarm`, session model configuration, and `ctx.connect()` flow intact.
2. Update `tests/test_agent.py` so it asserts the entrypoint now composes the HVAC controller/runtime boundary and no longer references the template assistant behavior.
3. Verify that the controller wiring leaves clear extension seams for S05 lifecycle orchestration rather than hardcoding post-call integration behavior into `src/agent.py`.
4. Run the combined S03 verification command plus Ruff to confirm the slice-level entrypoint composition is green.

## Must-Haves

- [ ] The starter `Assistant` class/template behavior is removed or no longer used by the runnable entrypoint.
- [ ] `src/agent.py` preserves the existing server/session bootstrap shape so later slices can add lifecycle orchestration without redoing S03.
- [ ] Entry-point verification proves real composition, not just module imports.

## Verification

- `uv run pytest tests/test_agent.py tests/test_prompts.py tests/test_conversation_controller.py`
- `uv run ruff check src/ tests/`

## Observability Impact

- Signals added/changed: Entry-point composition becomes test-visible through direct assertions on imported controller wiring instead of hidden runtime assumptions.
- How a future agent inspects this: Run the named tests and inspect `src/agent.py` composition if session startup behavior regresses.
- Failure state exposed: Stale starter wiring, broken controller imports, or accidental entrypoint shape drift becomes immediately detectable.

## Inputs

- `src/conversation/conversation_controller.py` — implemented S03 runtime controller to compose.
- `tests/test_agent.py` — updated entrypoint contract from T01.
- `src/agent.py` — current LiveKit server/session bootstrap to preserve.

## Expected Output

- `src/agent.py` — runnable entrypoint now starting the HVAC conversation controller.
- `tests/test_agent.py` — green composition test for the real controller entrypoint.
