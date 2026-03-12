# HVAC After-Hours Voice Agent

Operator runbook for Milestone M001 (S06 readiness).

## Setup

1. Install Python 3.12+ and [uv](https://docs.astral.sh/uv/).
2. Sync dependencies:
   ```bash
   uv sync --dev
   ```
3. Copy the environment template and fill in real credentials locally:
   ```bash
   cp .env.example .env.local
   ```
   > Keep secrets out of git. `.env.local` and `.env` are ignored.

## Environment Variables

The app loads `.env.local` first, then `.env` (`tests/conftest.py` and `src/agent.py`).

Required keys:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `GHL_API_TOKEN`
- `GHL_LOCATION_ID`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`

If GoHighLevel/Twilio keys are missing, runtime falls back to no-op provider stubs so local runs still complete.

## Run Commands

### Console mode (terminal-driven)

```bash
uv run python src/agent.py console
```

### Dev mode (LiveKit dev loop)

```bash
uv run python src/agent.py dev
```

## Verification Commands

Run these before handing off changes:

```bash
uv run pytest tests/test_s06_readiness.py tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider
uv sync --dev
uv run pytest
uv run ruff check src/
uv run ruff format --check src/
```

Minimum readiness checks enforced by tests:

```bash
uv run pytest tests/test_s06_readiness.py -q
uv run ruff check src/
uv run ruff format --check src/
```

## Demo Checklist

Use this script for milestone demo readiness.

### 1) Normal intake path

- Start in `console` mode.
- Simulate a typical after-hours HVAC issue (no safety terms).
- Provide name, callback number, issue summary, and callback time.
- Expected: call closes cleanly, CRM persistence is attempted, and no owner SMS is sent when `notify_owner=false`.

### 2) Safety escalation path

- Start a new call and include danger language (example: gas smell / CO alarm / sparks).
- Expected: immediate safety-first handoff behavior, finalized record still attempts CRM persistence, and owner SMS is sent when `notify_owner=true`.

### 3) Partial hang-up path

- Start intake and terminate early before all slots are confirmed.
- Expected: finalization still runs, call status is partial, and CRM persistence is still attempted.

## Expected Post-Call Outcomes

- **CRM record is always attempted** on finalized calls (complete or partial).
- **SMS is conditional**: sent only when `notify_owner=true` and skipped otherwise.
- **Provider failures are isolated**: one integration failure should not block the other provider path.

## Lifecycle Diagnostics and Troubleshooting

Primary diagnostics surfaces:

1. Structured lifecycle logs (`agent.lifecycle`) with phases:
   - `finalize_started`
   - `crm_result`
   - `sms_result`
   - `finalize_completed`
2. `CallLifecycle.snapshot()` for inspectable state during tests/debugging.

For targeted failure-path verification, run:

```bash
uv run pytest tests/test_call_lifecycle.py::test_lifecycle_records_structured_provider_failures_without_blocking_other_provider -q
```

All examples in this README are redacted and placeholder-safe by design.
