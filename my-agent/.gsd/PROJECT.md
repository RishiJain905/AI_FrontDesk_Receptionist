# Project

## What This Is

HVAC After-Hours Voice Intake Agent — a production-oriented LiveKit voice agent for after-hours (5 PM–9 AM) HVAC intake. It captures structured caller details via adaptive slot-filling, escalates immediately on danger signals, persists call outcomes to GoHighLevel, and sends owner SMS alerts when escalation rules match.

## Core Value

After-hours callers get a natural, safety-aware intake flow that avoids repetitive questioning, while the business receives structured CRM records (complete or partial calls) and timely owner alerts for urgent/safety scenarios.

## Current State

**All M001 implementation slices (S01–S06) are complete.**

Completed capability surfaces include:

- Typed domain/config contracts (`BusinessConfig`, `CallIntakeRecord`, slot/classification enums) and validated config loading
- Adaptive intake runtime (`SlotTracker`, `IntakePolicy`, `IntakeTask`) with live classification
- Safety-first controller handoff (`HVACIntakeAgent` → `SafetyAgent`) and deterministic prompt surfaces
- GoHighLevel + Twilio integrations with typed/redacted failure diagnostics
- Timezone-safe after-hours gate and idempotent lifecycle finalization with transcript assembly, caller-ID fallback, and provider isolation
- Release-readiness contracts (`tests/test_s06_readiness.py`), bootstrap artifacts (`README.md`, `.env.example`, `pyproject.toml`), and fully green quality gates (`pytest`, Ruff check/format)

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

- [x] M001: HVAC After-Hours Voice Agent — implementation complete through S06; remaining operational follow-up is live credential-backed UAT evidence capture (outside deterministic CI/local gates).
