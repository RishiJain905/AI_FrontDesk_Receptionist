---
id: T01
parent: S04
milestone: M001
provides:
  - RED proof boundary for S04 CRM, SMS, phone-normalization, and record-contract behavior
key_files:
  - tests/test_ghl_service.py
  - tests/test_sms_service.py
  - tests/test_phone_utils.py
  - tests/test_types.py
  - .gsd/milestones/M001/slices/S04/S04-PLAN.md
key_decisions:
  - S04 RED tests import services.crm.*, services.alerts.*, utils.phone, and utils.errors directly so missing runtime modules fail honestly at collection time
  - GoHighLevel proof locks search-create-update-note flow with deterministic mapper expectations and typed CrmError metadata
  - Twilio proof locks Basic Auth form posts, notify_owner/sms_sent skip rules, and typed SmsError metadata
patterns_established:
  - Shared phone normalization is the single asserted path for both GoHighLevel and Twilio payloads
  - Integration failure diagnostics must expose stable service, operation, and status_code fields rather than only free-form text
observability_surfaces:
  - uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py
  - uv run pytest tests/test_types.py
  - uv run ruff check src/ tests/
duration: 42m
verification_result: passed
completed_at: 2026-03-11T18:41:06.488224-04:00
blocker_discovered: false
---

# T01: Lock the S04 boundary with failing CRM, SMS, and phone-normalization tests

**Added RED S04 tests that define the GoHighLevel, Twilio, phone-normalization, and extended `CallIntakeRecord` contracts, with failures localized to the missing S04 runtime modules and fields.**

## What Happened

I extended `tests/test_types.py` so `CallIntakeRecord` now has an explicit RED contract for the planned S04 integration fields: `callback_time`, `customer_type`, `transcript`, `ai_summary`, `notify_owner`, and `sms_sent`. The updated tests require those fields to default to `None` and to round-trip when provided.

I created `tests/test_phone_utils.py` as the shared normalization boundary. It imports `utils.phone.normalize_phone` directly and defines the required behavior for local 10-digit, dashed, spaced, leading-1, already-E.164, and invalid/blank inputs.

I created `tests/test_ghl_service.py` as the GoHighLevel RED proof. It imports the planned `services.crm.ghl_service`, `services.crm.mappers`, and `utils.errors` modules directly, locks deterministic contact-payload and note formatting, and uses `httpx.MockTransport` expectations for search, create, update, and note requests. The failure-path test requires a typed `CrmError` with stable `service`, `operation`, and `status_code` metadata.

I created `tests/test_sms_service.py` as the Twilio RED proof. It imports the planned `services.alerts.sms_service` and `utils.errors` modules directly, locks the owner-alert message shape, requires Twilio `Messages.json` form posts with Basic Auth, asserts the skip behavior when `notify_owner` is false or `sms_sent` is already true, and requires a typed `SmsError` with stable metadata.

## Verification

- Ran `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py`
  - Result: FAIL as expected.
  - Evidence: collection failed on direct S04 imports with `ModuleNotFoundError: No module named 'services'` and `ModuleNotFoundError: No module named 'utils'`.
  - Interpretation: the RED tests are wired to the real planned S04 module paths and fail because the S04 runtime has not been implemented yet.
- Ran `uv run pytest tests/test_types.py`
  - Result: FAIL as expected.
  - Evidence: `CallIntakeRecord` is missing `callback_time`, and the constructor rejects the new integration keyword arguments.
  - Interpretation: the record-contract RED test is honest and localizes the missing S04 fields immediately.
- Ran `uv run ruff check src/ tests/`
  - Result: PASS (`All checks passed!`).

## Diagnostics

Future inspection path:
- Run `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py`.
- If collection fails on `services.*` or `utils.*`, the S04 runtime modules still do not exist.
- If `tests/test_types.py` fails on missing attributes or constructor kwargs, `CallIntakeRecord` has not been extended to the S04 contract yet.
- Once imports exist, failures should localize cleanly to `test_phone_utils`, `test_ghl_service`, or `test_sms_service` for request shape, note formatting, skip behavior, or typed error metadata drift.

## Deviations

None.

## Known Issues

- `src/services/crm/ghl_service.py` does not exist yet.
- `src/services/crm/mappers.py` does not exist yet.
- `src/services/alerts/sms_service.py` does not exist yet.
- `src/utils/phone.py` does not exist yet.
- `src/utils/errors.py` does not exist yet.
- `src/hvac_types/call_intake_record.py` does not yet expose the S04 integration fields required by the new tests.

## Files Created/Modified

- `tests/test_ghl_service.py` — RED GoHighLevel mapper and request-shape tests for search/create/update/note flow plus typed CRM failure diagnostics.
- `tests/test_sms_service.py` — RED Twilio send/skip/error tests with Basic Auth and concise owner-alert text expectations.
- `tests/test_phone_utils.py` — RED phone-normalization contract shared by both integrations.
- `tests/test_types.py` — extended `CallIntakeRecord` contract assertions for the new optional S04 integration fields.
- `.gsd/milestones/M001/slices/S04/S04-PLAN.md` — marked T01 complete.
