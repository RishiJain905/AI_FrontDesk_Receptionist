# Project

## What This Is

HVAC After-Hours Voice Intake Agent — a production-oriented LiveKit voice agent for after-hours (5 PM–9 AM) HVAC intake. It captures structured caller details via adaptive slot-filling, escalates immediately on danger signals, persists call outcomes to GoHighLevel, and sends owner SMS alerts when escalation rules match.

## Core Value

After-hours callers get a natural, safety-aware intake flow that avoids repetitive questioning, while the business receives structured CRM records (complete or partial calls) and timely owner alerts for urgent/safety scenarios.

## Current State

**M001 implementation is complete through S06 and all deterministic quality gates are green.**

Fresh verification evidence in this completion unit:

- `uv run pytest` → `131 passed`
- `uv run ruff check src/ tests/` → pass
- `uv run ruff format --check src/` → pass

Remaining gap to mark milestone verification fully passed:

- Live credential-backed operational proof for real GoHighLevel contact/note creation and real Twilio SMS delivery (tracked as post-slice UAT follow-up).

## Architecture / Key Patterns

- Python + LiveKit Agents SDK (~1.4) with AgentTask/function-tool workflow
- `src/agent.py` as the runtime entrypoint
- Config-driven behavior (business identity, hours, danger/urgency keywords, owner phone)
- Lifecycle snapshot + structured event phases for post-call diagnostics
- Integration failure isolation (CRM/SMS failures do not crash call finalization)
- uv-managed environment; pytest + Ruff quality gates

## Capability Contract

See `.gsd/REQUIREMENTS.md` for authoritative requirement status and proof mapping.

## Milestone Sequence

- [x] M001: HVAC After-Hours Voice Agent — implementation complete; deterministic gates pass; live provider UAT evidence still required for full operational verification closure.
