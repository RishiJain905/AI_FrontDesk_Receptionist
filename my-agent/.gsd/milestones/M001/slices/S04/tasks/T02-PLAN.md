---
estimated_steps: 5
estimated_files: 7
---

# T02: Extend the integration-facing record contract and shared utilities

**Slice:** S04 — GoHighLevel CRM and SMS Alert Integrations
**Milestone:** M001

## Description

Build the common S04 boundary that both providers depend on: richer intake-record fields, phone normalization, typed integration errors, and provider-agnostic protocols. This keeps the provider tasks focused on real external wiring instead of reinventing the same support logic twice.

## Steps

1. Extend `src/hvac_types/call_intake_record.py` with the optional integration fields needed by R005/R006 (`callback_time`, `customer_type`, `transcript`, `ai_summary`, `notify_owner`, `sms_sent`) while preserving default-`None`/`False` compatibility for existing callers.
2. Add `src/utils/phone.py` with `normalize_phone(number) -> str` that handles the North American formats currently emitted by intake and raises a stable validation error for unusable inputs.
3. Add `src/utils/errors.py` with `IntegrationError`, `CrmError`, and `SmsError`, carrying stable metadata like `service`, `operation`, `status_code`, and a redacted detail surface.
4. Add `src/services/crm/crm_service.py` and `src/services/alerts/alert_service.py` defining the async protocol boundaries S05 will call (`upsert_contact`, `attach_call_note`, `send_owner_sms`).
5. Run the record and phone tests, iterating until the shared-contract portion of the RED suite is green and ready for the provider-specific implementations.

## Must-Haves

- [ ] New `CallIntakeRecord` fields are optional and default-safe so existing S01–S03 code keeps constructing records without immediate churn.
- [ ] `normalize_phone()` is the only shared normalization path and is suitable for both GoHighLevel matching and Twilio outbound sends.
- [ ] Integration errors expose stable metadata without leaking raw auth secrets or dumping full transcripts into exception messages.
- [ ] Protocols stay provider-agnostic so S05 can depend on behavior, not concrete Twilio/GoHighLevel classes.

## Verification

- `uv run pytest tests/test_types.py tests/test_phone_utils.py`
- Expected result: PASS, proving the record contract, shared phone logic, and error/protocol imports are ready for provider-specific implementation.

## Observability Impact

- Signals added/changed: Stable typed error envelope and a single phone-normalization boundary shared across integrations.
- How a future agent inspects this: Import `normalize_phone` or the error classes directly in tests/REPL; inspect `CallIntakeRecord` defaults in `tests/test_types.py`.
- Failure state exposed: Invalid phone handling and provider failures now localize to explicit utility/error contracts instead of being buried in HTTP client exceptions.

## Inputs

- `tests/test_types.py` — updated contract expectations from T01.
- `tests/test_phone_utils.py` — shared normalization behavior required by both providers.
- `src/hvac_types/classification.py` — enum values that later mapper and SMS formatting must carry through unchanged.
- Decision D006 — integrations use async `httpx`, so protocols and errors should fit async service implementations.

## Expected Output

- `src/hvac_types/call_intake_record.py` — richer optional integration record fields with backward-compatible defaults.
- `src/utils/phone.py` — shared normalization function for CRM and SMS.
- `src/utils/errors.py` — typed, redacted integration error surfaces.
- `src/services/crm/crm_service.py` — CRM provider protocol.
- `src/services/alerts/alert_service.py` — alert provider protocol.
