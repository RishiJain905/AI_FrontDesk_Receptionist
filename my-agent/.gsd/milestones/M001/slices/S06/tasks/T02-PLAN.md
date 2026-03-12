---
estimated_steps: 5
estimated_files: 3
---

# T02: Implement README, env example, and pyproject bootstrap artifacts

**Slice:** S06 — Full Test Suite and Demo Readiness
**Milestone:** M001

## Description

Implement the missing readiness artifacts required by S06 and CI reproducibility: an operator-facing README, safe environment template, and root project manifest consumable by `uv sync --dev`.

## Steps

1. Create `README.md` with concise sections for setup, required environment variables, run commands (`console` and `dev`), verification commands, and a demo checklist (normal intake, safety call, partial hang-up).
2. Include expected post-call outcomes in README (CRM record always attempted, SMS only when `notify_owner=true`, and where to inspect lifecycle diagnostics).
3. Create `.env.example` with all required key names for LiveKit, GoHighLevel, and Twilio using placeholder values only.
4. Create `pyproject.toml` with `[project]` metadata, Python constraint, runtime dependencies used by `src/` imports, and dev dependencies/tool settings for pytest + Ruff.
5. Run the readiness tests and `uv sync --dev`; adjust artifact content until both pass.

## Must-Haves

- [ ] README is actionable for a first-time operator and includes milestone-required verification and demo steps.
- [ ] `.env.example` includes required keys without exposing any real secret material.
- [ ] `pyproject.toml` supports clean-environment dependency sync using CI-equivalent command (`uv sync --dev`).

## Verification

- `uv run pytest tests/test_s06_readiness.py -q`
- `uv sync --dev`

## Observability Impact

- Signals added/changed: README now documents where lifecycle diagnostics are surfaced (`CallLifecycle.snapshot()` + structured logs) during demo troubleshooting.
- How a future agent inspects this: Read `README.md` for runbook/debug path; run `uv sync --dev` to validate bootstrap readiness.
- Failure state exposed: Missing dependency metadata or incomplete env/run instructions now fail readiness tests and/or sync command.

## Inputs

- `tests/test_s06_readiness.py` — RED contract introduced in T01.
- `src/agent.py` — source of truth for runtime commands and provider env variable expectations.
- `.github/workflows/tests.yml` / `.github/workflows/ruff.yml` — CI bootstrap and quality-gate contract.

## Expected Output

- `README.md` — complete S06 usage/demo/verification runbook.
- `.env.example` — safe, complete environment key template.
- `pyproject.toml` — reproducible project manifest for `uv sync --dev` and quality tooling.
