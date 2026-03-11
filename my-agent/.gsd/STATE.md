# GSD State

**Active Milestone:** M001 — HVAC After-Hours Voice Agent
**Active Slice:** S06 — Full Test Suite and Demo Readiness (next)
**Active Task:** None
**Phase:** S05 is complete and closed. Runtime now includes after-hours gate decisions, finalize-once lifecycle orchestration, transcript assembly, caller-ID fallback semantics, and entrypoint wiring with provider isolation diagnostics.

## Recent Decisions

- D031: S05 verification uses pytest seams for gate math, lifecycle finalization, provider isolation, and entrypoint composition instead of live telephony during the slice gate.
- D032: S05 extends shared contracts with config-driven after-hours fields and explicit caller-ID/callback-confirmation state.
- D033: `CallLifecycle` exposes stable snapshot/logger diagnostics for gate, transcript, finalize, CRM, and SMS outcomes using redacted metadata.
- D034: Keep `zoneinfo` as primary timezone resolver, with deterministic Toronto fallback only for injected-time checks when tzdata is unavailable.
- D035: Lifecycle finalization uses committed conversation events + controller diagnostics as source-of-truth with redacted snapshot/log outputs.
- D036: Entrypoint composes real GoHighLevel/Twilio providers when configured and protocol-compatible no-op fallbacks when credentials are absent, preserving runnable lifecycle wiring in local/dev.

## Blockers

- None.

## Next Action

Start S06: run full milestone verification gates (`uv run pytest`, `uv run ruff check src/`, `uv run ruff format --check src/`), complete live provider/UAT proof, and finalize demo/documentation readiness.
