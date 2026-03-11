---
estimated_steps: 4
estimated_files: 4
---

# T01: Lock the S04 boundary with failing CRM, SMS, and phone-normalization tests

**Slice:** S04 — GoHighLevel CRM and SMS Alert Integrations
**Milestone:** M001

## Description

Create the RED proof boundary for S04 before any integration implementation lands. The tests must define the exact request shapes, skip rules, new record fields, and diagnostic expectations that prove the slice owns R005/R006 rather than merely adding helper scaffolding.

## Steps

1. Add `tests/test_types.py` assertions for the new optional `CallIntakeRecord` integration fields so missing record data becomes an honest failure immediately.
2. Create `tests/test_phone_utils.py` covering local 10-digit, dashed, spaced, leading-1, already-E.164, and invalid/blank phone normalization behavior.
3. Create `tests/test_ghl_service.py` using `httpx.MockTransport` to assert GoHighLevel search, create, update, and note requests (method, URL, headers, and payload) plus a typed `CrmError` failure-path assertion.
4. Create `tests/test_sms_service.py` using `httpx.MockTransport` to assert Twilio send, skip-when-disabled/already-sent, and typed `SmsError` failure behavior, then run the named pytest command and confirm it fails only because S04 code is missing.

## Must-Haves

- [ ] The tests import the planned S04 modules directly (`services.crm.*`, `services.alerts.*`, `utils.phone`, `utils.errors`) so missing implementation fails honestly at collection or import time.
- [ ] At least one CRM test asserts deterministic note content includes classification fields, callback time, transcript, and AI summary.
- [ ] At least one SMS test asserts the service skips outbound requests when `notify_owner` is false or `sms_sent` is already true.
- [ ] At least one failure-path assertion checks stable error metadata rather than only matching a free-form message string.

## Verification

- `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py`
- Expected initial result: FAIL because S04 modules/fields are not implemented yet, while the tests themselves express the real integration contract.

## Observability Impact

- Signals added/changed: Test-visible diagnostic expectations for `service`, `operation`, and `status_code` on integration failures.
- How a future agent inspects this: Run the named pytest command and localize regressions by file (`test_phone_utils`, `test_ghl_service`, `test_sms_service`, or `test_types`).
- Failure state exposed: Incorrect request shape, missing headers, wrong skip behavior, or vague error surfaces will fail with targeted assertions instead of hidden runtime drift.

## Inputs

- `src/hvac_types/call_intake_record.py` — current record contract that S04 must extend without breaking defaults.
- `src/hvac_types/business_config.py` — source of `owner_phone` and other config-driven values the services must consume.
- S04 research summary — establishes GoHighLevel v2 headers/flow, Twilio Basic Auth, and the need for `httpx.MockTransport`-based proof.
- `.gsd/REQUIREMENTS.md` — owned requirement targets R005 and R006 plus failure-isolation support for R009.

## Expected Output

- `tests/test_ghl_service.py` — RED CRM integration tests for upsert, note attachment, and typed failure diagnostics.
- `tests/test_sms_service.py` — RED SMS integration tests for send, skip, and typed failure diagnostics.
- `tests/test_phone_utils.py` — RED phone normalization tests shared by both integrations.
- `tests/test_types.py` — updated RED contract assertions for the new `CallIntakeRecord` fields.
