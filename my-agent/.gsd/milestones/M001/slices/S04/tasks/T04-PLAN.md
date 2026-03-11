---
estimated_steps: 5
estimated_files: 4
---

# T04: Implement Twilio owner alerts and close the slice verification gate

**Slice:** S04 — GoHighLevel CRM and SMS Alert Integrations
**Milestone:** M001

## Description

Finish S04 by implementing the real SMS provider boundary and proving the full slice verification gate. This closes R006 and leaves S05 with provider-backed protocols it can call during finalization without embedding any Twilio or CRM transport logic in the lifecycle.

## Steps

1. Add `src/services/alerts/sms_service.py` implementing `TwilioSmsService` with constructor-injected `httpx.AsyncClient`, account SID, auth token, and from-number configuration.
2. Format concise owner-alert text from `CallIntakeRecord` and `BusinessConfig`, carrying caller name, callback number, issue summary, urgency, and danger context while remaining short enough for an actionable SMS.
3. Implement skip logic so no HTTP request is sent when `notify_owner` is false or `sms_sent` is already true, and normalize both destination and sender numbers through the shared phone utility.
4. Wrap Twilio request/status failures in `SmsError` with stable operation/status metadata and keep the implementation isolated behind `AlertService` so CRM logic is never imported or coupled here.
5. Run the full S04 verification command plus Ruff and stop only when the whole slice gate is green.

## Must-Haves

- [ ] Twilio sends use direct async HTTP with Basic Auth against `Messages.json`; no sync SDK is introduced.
- [ ] SMS content is concise, action-oriented, and includes the minimum owner-alert facts required by R006.
- [ ] Skip conditions prevent duplicate or disabled alerts before any outbound request is attempted.
- [ ] SMS failures surface `SmsError` cleanly and do not introduce any dependency on CRM code paths.

## Verification

- `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py`
- `uv run ruff check src/ tests/`
- Expected result: PASS, proving the provider-specific SMS boundary works and the full S04 slice gate is green.

## Observability Impact

- Signals added/changed: Alert operations become inspectable as `send_owner_sms` or `skip_owner_sms` outcomes with stable failure metadata.
- How a future agent inspects this: Run `tests/test_sms_service.py`, inspect returned message IDs / skip results, or catch `SmsError` directly in downstream orchestration.
- Failure state exposed: Wrong skip logic, malformed Basic Auth requests, or Twilio status failures become explicit without coupling to CRM or session runtime.

## Inputs

- `src/services/alerts/alert_service.py` — provider-agnostic alert boundary from T02.
- `src/utils/phone.py` and `src/utils/errors.py` — shared normalization and error surfaces.
- `tests/test_sms_service.py` — RED SMS contract from T01.
- `src/hvac_types/call_intake_record.py` and `src/hvac_types/business_config.py` — caller/owner data required to format the outbound alert.

## Expected Output

- `src/services/alerts/sms_service.py` — async Twilio provider with skip logic and typed failure handling.
- `src/services/alerts/__init__.py` — exports for the alert provider boundary.
- `tests/test_sms_service.py` — green SMS contract tests closing R006 at the slice proof boundary.
