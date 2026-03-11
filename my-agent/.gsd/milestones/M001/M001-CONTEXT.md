# M001: HVAC After-Hours Voice Agent — Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

## Project Description

Replace the generic LiveKit starter agent with a full HVAC-specific after-hours intake agent. The codebase is a Python LiveKit Agents project (livekit-agents~=1.4) using uv. The `src/agent.py` file is the entrypoint and must remain so (Dockerfile depends on it). All new modules live under `src/` alongside agent.py.

## Why This Milestone

The user provided a complete product spec for an HVAC after-hours voice intake demo. The starter agent does nothing HVAC-specific — no slot-filling, no CRM, no SMS, no safety branch, no after-hours gate. This milestone delivers the full specified system as a single coherent build.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Connect the agent to a SIP phone line (or test with console mode), call after hours, and have the agent naturally capture name, callback number, issue summary, and callback time
- Say "I smell gas" and immediately get safety guidance instead of the normal intake sequence
- After the call, see a structured contact record in GoHighLevel with transcript and AI summary attached
- Receive an SMS on the owner alert phone when urgency rules match
- Change `hvac_demo_config.py` values (business name, keywords, hours, phone) without touching any core logic

### Entry point / environment

- Entry point: `uv run python src/agent.py dev` (dev mode) or `uv run python src/agent.py console` (terminal test)
- Environment: local dev with LiveKit Cloud credentials; SIP telephony for real calls
- Live dependencies involved: LiveKit Cloud, GoHighLevel API v2, SMS provider (Twilio or similar), phone number for SIP

## Completion Class

- Contract complete means: all AgentTask slot-filling logic works in tests; classification assigns correct categories and urgency; after-hours gate logic is timezone-correct
- Integration complete means: GoHighLevel contact create/update and note attachment work with real credentials; SMS sends with real credentials
- Operational complete means: full call lifecycle (connect → intake → safety branch if needed → finalize → CRM → SMS) runs without crash on partial/full calls; CRM and SMS failures are isolated

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- A full console test session captures all required slots, writes a GoHighLevel contact with transcript and note, and does not send SMS when urgency is standard
- A console test session starting with "I smell gas" triggers the safety branch, sets dangerDetected=true, writes the CRM record, and sends the owner SMS
- A call that ends halfway through (hang-up simulation) still writes a partial record to GoHighLevel with callStatus=partial
- After-hours gate correctly blocks/allows the agent at the time boundary across midnight in America/Toronto

## Risks and Unknowns

- GoHighLevel v2 API payload shape for contact upsert and note attachment — need to verify field names and auth headers at implementation time
- SMS provider selection — spec does not name a specific provider; Twilio is the obvious default; must validate env var naming at implementation time
- LiveKit AgentTask + handoff interaction for mid-call safety branch switch — must confirm session.update_agent pattern works in the version shipped in livekit-agents~=1.4
- Whether `TaskGroup` (beta.workflows) is available in livekit-agents~=1.4 — may need to use sequential AgentTask pattern instead

## Existing Codebase / Prior Art

- `src/agent.py` — Current entrypoint; must be transformed not replaced; keep AgentServer/JobContext/prewarm pattern
- `pyproject.toml` — Defines dependencies; will need httpx (or aiohttp), pytz (or zoneinfo), pytest-asyncio
- `tests/test_agent.py` — Existing eval tests; new tests must follow the same `AgentSession` + `inference.LLM` pattern
- `.env.example` — Only LiveKit creds today; must be extended for GHL and SMS creds

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001 — Primary user loop delivered here
- R002 — Slot-filling conversation model delivered here
- R003 — Safety branch delivered here
- R004 — Background classification delivered here
- R005 — GoHighLevel integration delivered here
- R006 — SMS alerting delivered here
- R007 — After-hours gate delivered here
- R008 — Config-driven settings foundation delivered here
- R009 — Graceful failure handling delivered here
- R010 — Full test coverage delivered here

## Scope

### In Scope

- All items from spec sections 1–27
- Full module structure per spec section 18 (translated to Python)
- Adaptive slot-filling intake conversation
- Safety emergency branch with immediate override
- Background live classification during call
- Final post-call classification producing aiSummary, issueCategory, urgencyLevel
- GoHighLevel CRM: find/create contact, attach note with structured fields + transcript + summary
- SMS alert: concise owner notification when notifyOwner=true
- After-hours gate with timezone-safe overnight window
- HVAC demo config as default profile
- Complete pytest test suite covering all major scenarios

### Out of Scope / Non-Goals

- FAQ answering, appointment scheduling, dispatch orchestration
- Email alerts
- Admin UI or multi-tenant dashboard
- Multilingual support
- GoHighLevel v1 API (use v2)

## Technical Constraints

- Python only (no TypeScript despite spec using TS notation for type definitions)
- Must retain `src/agent.py` as the entrypoint (Dockerfile requirement)
- livekit-agents~=1.4 — do not upgrade major version
- All secrets via environment variables; no hardcoded credentials anywhere
- uv for all dependency management
- Ruff for formatting/linting

## Integration Points

- LiveKit Cloud — WebSocket session transport; LiveKit Inference for STT/LLM/TTS
- GoHighLevel API v2 — REST API; auth via API key or OAuth token (Bearer); base URL: https://services.leadconnectorhq.com or https://rest.gohighlevel.com/v1
- SMS provider (Twilio default) — REST API; configured via environment variables
- SIP telephony — LiveKit SIP trunks; caller ID available from participant metadata

## Open Questions

- GoHighLevel API v2 exact auth pattern (API key header vs Bearer token) — verify at implementation time against docs.gohighlevel.com
- SMS provider exact env var names — default to Twilio; TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
- Whether `zoneinfo` (Python 3.9+ stdlib) is sufficient for timezone handling or if pytz is needed — prefer zoneinfo since project requires Python >=3.10
