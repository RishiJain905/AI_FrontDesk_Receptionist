---
estimated_steps: 5
estimated_files: 5
---

# T04: Wire the S05 lifecycle into the real agent entrypoint and close the slice gate

**Slice:** S05 — Call Lifecycle Orchestration and After-Hours Gate
**Milestone:** M001

## Description

Compose the new S05 boundaries into the real runtime entrypoint so the project no longer has a standalone controller only. This task closes the loop by making `src/agent.py` the actual after-hours lifecycle entrypoint and proving that the slice verification gate is green.

## Steps

1. Update `src/agent.py` to load `.env.local` and `.env` explicitly, keeping the existing LiveKit bootstrap shape while adding S05 runtime composition seams.
2. Instantiate the after-hours gate, runtime services, and `CallLifecycle` around the `AgentSession`, preserving `build_runtime_agent()` as the controller-construction seam introduced in S03.
3. Wire any available caller/session metadata into the lifecycle so caller-ID fallback has a real entrypoint path, and subscribe the lifecycle to session events before or around `session.start(...)`.
4. Trigger `session.generate_reply(...)` after `session.start(...)` so inbound callers hear the opening after-hours greeting without needing to speak first, and keep the outside-hours branch as a logged graceful pass-through rather than a crash.
5. Run the full S05 pytest gate plus Ruff and stop only when the slice-level verification is green.

## Must-Haves

- [ ] `src/agent.py` performs real composition with the new gate/lifecycle surfaces instead of leaving them as test-only helpers.
- [ ] Dotenv behavior is explicit and matches the test/runtime expectation for `.env.local` plus `.env`.
- [ ] The initial greeting is triggered from the real session runtime after start, closing the current telephony silence gap.
- [ ] Outside-hours behavior is explicit and observable even if it is currently a graceful pass-through rather than a separate daytime-routing system.

## Verification

- `uv run pytest tests/test_after_hours_gate.py tests/test_call_lifecycle.py tests/test_agent.py tests/test_types.py`
- `uv run ruff check src/ tests/`
- Expected result: PASS, proving the real entrypoint now composes the S05 lifecycle and the slice gate is closed.

## Observability Impact

- Signals added/changed: Entrypoint-level gate decision and lifecycle wiring become inspectable through AST/runtime tests plus structured logger initialization.
- How a future agent inspects this: Run `tests/test_agent.py` for composition regressions and inspect the lifecycle/gate logger output during local console runs.
- Failure state exposed: Missing greeting trigger, missing lifecycle attachment, or stale dotenv composition will fail via explicit wiring assertions rather than surfacing as telephony silence later.

## Inputs

- `src/agent.py` — existing S03 entrypoint that still only starts the controller.
- `src/orchestration/after_hours_gate.py` and `src/orchestration/call_lifecycle.py` — new runtime boundaries from T02/T03.
- `tests/test_agent.py` — RED entrypoint wiring contract from T01.
- Decision D024 — `build_runtime_agent()` remains the stable seam for controller construction.

## Expected Output

- `src/agent.py` — real S05 runtime entrypoint with gate, lifecycle, and greeting composition.
- `tests/test_agent.py` — green proof that the entrypoint wiring matches the S05 runtime contract.
- `tests/test_call_lifecycle.py` — green runtime-seam coverage for the fully wired lifecycle behavior.
