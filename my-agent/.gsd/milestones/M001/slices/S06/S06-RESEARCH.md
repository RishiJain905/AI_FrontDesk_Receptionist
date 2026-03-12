# S06 — Research

**Date:** 2026-03-11

## Summary

S06 is the milestone hardening slice: it **owns R010 (full behavioral test coverage and quality gates)** and supports closure evidence for **R001–R009** by proving the integrated system is shippable and demo-ready. Based on current repo state, behavior coverage is strong and broad (`uv run pytest` currently passes all 121 tests), including normal intake, safety handoff, partial lifecycle finalization, no-heat urgency classification, outside-hours gate math, and CRM/SMS failure isolation.

The two immediate blockers to S06 DoD are operational/readiness quality gates, not core logic: (1) `uv run ruff format --check src/` currently fails (9 files would be reformatted), and (2) required demo/readme artifacts are incomplete (`README.md` is missing entirely, and `.env.example` is missing). There is also a reproducibility risk: `pyproject.toml` is missing from repo root while CI workflows still run `uv sync --dev`, which will fail in clean environments unless project metadata is restored.

Primary recommendation: execute S06 as a release-readiness pass in this order — **format stabilization → docs + demo runbook → manifest/env-example hygiene → final full-suite verification evidence**. Avoid new architecture work in S06; all remaining risk is around repeatability, operator guidance, and objective gate evidence.

## Requirement Targeting (Active)

- **Owned by S06:**
  - **R010 — Test Coverage** (primary)
- **Directly supported by S06 verification closure:**
  - **R001/R002/R003/R004** via conversation and slot/classification eval suites
  - **R005/R006** via CRM/SMS contract tests + lifecycle integration behavior
  - **R007** via after-hours boundary tests + entrypoint wiring assertions
  - **R008** via config contract validation tests and runtime wiring checks
  - **R009** via partial-finalize and provider-isolation lifecycle tests

## Recommendation

Use a strict readiness checklist for S06:

1. **Formatting gate first**
   - Run: `uv run ruff format src/ tests/` (or minimally `src/` for milestone DoD), then re-run:
   - `uv run ruff check src/`
   - `uv run ruff format --check src/`
2. **Documentation/demo readiness**
   - Add `README.md` with:
     - setup + env requirements,
     - `console` and `dev` run commands,
     - verification commands,
     - demo script for normal call + safety call + partial hang-up,
     - expected CRM/SMS outcomes.
3. **Environment/bootstrap hygiene**
   - Add/update `.env.example` with all required vars (LiveKit + GHL + Twilio).
   - Restore/confirm project manifest (`pyproject.toml`) expected by CI `uv sync --dev`.
4. **Final evidence run (fresh)**
   - `uv run pytest`
   - `uv run ruff check src/`
   - `uv run ruff format --check src/`
   - Capture command output in S06 execution artifacts before completion claim.

## Don’t Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| End-to-end call completion/failure behavior | `src/orchestration/call_lifecycle.py` + `tests/test_call_lifecycle.py` | Already provides finalize-once, caller-ID fallback, CRM/SMS isolation, and inspectable snapshot diagnostics. |
| Safety-switch correctness | `tests/test_conversation_controller.py` handoff assertions (`agent_handoff`) | Explicitly validates runtime handoff event semantics instead of prompt-only wording checks. |
| After-hours boundary correctness | `src/orchestration/after_hours_gate.py` + `tests/test_after_hours_gate.py` | Deterministic injected-time boundary tests already cover midnight-crossing logic. |
| CRM/SMS payload contracts | `tests/test_ghl_service.py` + `tests/test_sms_service.py` using `httpx.MockTransport` | Stable, deterministic request-shape proof without flaky live network dependence. |
| Entrypoint composition checks | `tests/test_agent.py` (AST assertions) | Fast guard against starter-template regressions in `src/agent.py` wiring. |

## Existing Code and Patterns

- `src/agent.py` — canonical runtime composition (dotenv load, gate check, lifecycle attach, provider composition/fallback, initial greeting).
- `src/orchestration/call_lifecycle.py` — authoritative post-call path for partial/complete status, transcript capture, CRM persistence, SMS send/skip/error.
- `src/orchestration/after_hours_gate.py` — pure `is_after_hours(config, now=...)` API with deterministic behavior for tests.
- `tests/test_conversation_controller.py` — strongest safety branch proof (explicit handoff event + emergency-first response intent).
- `tests/test_intake_task.py` — adaptive slot-filling and tentative-confirmation guard coverage.
- `tests/test_slot_filling.py` — deterministic no-heat urgency and danger keyword classification coverage.
- `tests/test_call_lifecycle.py` — partial finalization, duplicate-finalize idempotence, and provider failure isolation.
- `.github/workflows/tests.yml` / `.github/workflows/ruff.yml` — CI gate intent (currently expects `uv sync --dev` + pytest/ruff enforcement).

## Constraints

- `src/agent.py` must remain the runtime entrypoint (milestone + Docker coupling).
- LiveKit eval tests use real model calls (`inference.LLM("openai/gpt-4.1-mini")`), so test execution depends on valid env credentials.
- S06 DoD explicitly requires `uv run ruff check src/` and `uv run ruff format --check src/` success.
- Current repository state lacks root `pyproject.toml`, which conflicts with existing CI workflow commands (`uv sync --dev`).

## Common Pitfalls

- **Passing pytest but failing format gate** — `ruff check` passing is insufficient; `ruff format --check` must also pass.
- **Assuming demo readiness from no-op providers** — `src/agent.py` intentionally falls back to no-op CRM/SMS when creds are absent; real demo proof must run with configured providers.
- **Treating AST-only entrypoint tests as runtime proof** — `tests/test_agent.py` validates structure, not live call behavior; keep lifecycle/conversation tests as operational evidence.
- **Skipping docs closure** — roadmap requires README usage/demo instructions; no README means S06 is not truly demo-ready.

## Open Risks

- **Immediate blocker:** `uv run ruff format --check src/` currently fails (9 files would reformat).
- **Documentation blocker:** `README.md` missing despite S06 requirement for usage instructions.
- **Bootstrap risk:** `pyproject.toml` missing while CI expects `uv sync --dev`; clean-environment reproducibility is uncertain.
- **Operational proof gap:** live GoHighLevel + Twilio end-to-end demo evidence is still pending despite strong mock-transport tests.
- **Eval stability risk:** LLM-judged conversational tests can vary with upstream model/provider behavior; keep deterministic guards and avoid unnecessary prompt churn late in S06.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LiveKit Agents | installed skill `livekit-agents` | installed |
| GoHighLevel API | none found (`npx skills find "GoHighLevel"`) | none found |
| Twilio | `sickn33/antigravity-awesome-skills@twilio-communications` | available — install with `npx skills add sickn33/antigravity-awesome-skills@twilio-communications` |
| Pytest | `github/awesome-copilot@pytest-coverage` | available — install with `npx skills add github/awesome-copilot@pytest-coverage` |
| Ruff | `laurigates/claude-plugins@ruff-linting` (and `@ruff-formatting`) | available — install with `npx skills add laurigates/claude-plugins@ruff-linting` |

## Sources

- Full-suite baseline currently green (`121 passed`) (source: local command `uv run pytest`).
- Ruff lint gate currently passes for source tree (source: local command `uv run ruff check src/`).
- Ruff format gate currently fails for source tree (`9 files would be reformatted`) (source: local command `uv run ruff format --check src/`).
- README/doc artifact gap confirmed (`README.md` missing) (source: local filesystem check in repo root).
- CI workflow expects `uv sync --dev` + pytest (source: `.github/workflows/tests.yml`).
- CI workflow enforces `ruff check` + `ruff format --check` (source: `.github/workflows/ruff.yml`).
- LiveKit docs confirm session event model (`conversation_item_added`, `close`) and event-driven transcript hooks (source: https://docs.livekit.io/agents/build/events and https://docs.livekit.io/agents/logic/sessions via Context7 `/websites/livekit_io_agents`).
- Ruff docs confirm `format --check` semantics and exit codes (`1` when formatting would change files) (source: https://github.com/astral-sh/ruff/blob/main/docs/formatter.md via Context7 `/astral-sh/ruff`).
- Pytest docs support marker-based separation for optional slow/acceptance gates if S06 introduces live integration test strata (source: https://github.com/pytest-dev/pytest docs via Context7 `/pytest-dev/pytest`).
