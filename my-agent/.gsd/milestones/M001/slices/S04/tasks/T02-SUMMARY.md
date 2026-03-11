---
id: T02
parent: S04
milestone: M001
provides:
  - Shared S04 record, phone, error, and protocol contracts that provider implementations can build on without changing existing callers
key_files:
  - src/hvac_types/call_intake_record.py
  - src/utils/phone.py
  - src/utils/errors.py
  - src/services/crm/crm_service.py
  - src/services/alerts/alert_service.py
  - .gsd/milestones/M001/slices/S04/S04-PLAN.md
  - .gsd/DECISIONS.md
key_decisions:
  - `normalize_phone()` returns normalized E.164 output for supported North American inputs and `None` for unusable values; provider layers will turn unusable numbers into typed CRM/SMS failures when required
patterns_established:
  - Shared integration utilities now expose one phone-normalization path, one redacted typed-error envelope, and provider-agnostic async protocols for CRM and alert orchestration
observability_surfaces:
  - uv run pytest tests/test_types.py tests/test_phone_utils.py
  - uv run python - <<'PY' ... import utils.errors / services.* protocols ... PY
  - uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py
  - uv run ruff check src/ tests/
duration: 25m
verification_result: passed
completed_at: 2026-03-11T18:44:23.903657-04:00
blocker_discovered: false
---

# T02: Extend the integration-facing record contract and shared utilities

**Extended `CallIntakeRecord`, added shared phone/error utilities, and introduced provider-agnostic CRM/alert protocols so the S04 provider work can build on stable imports and typed diagnostics.**

## What Happened

I extended `src/hvac_types/call_intake_record.py` with the six optional S04 integration fields: `callback_time`, `customer_type`, `transcript`, `ai_summary`, `notify_owner`, and `sms_sent`. All keep the existing default-safe dataclass behavior so older S01–S03 call sites can still construct `CallIntakeRecord()` without churn.

I added `src/utils/phone.py` with `normalize_phone(number)`, which normalizes the North American formats locked by the RED tests into `+1XXXXXXXXXX` E.164 output and returns `None` for unusable input. That matches the current shared contract used by the slice tests and gives both CRM matching and SMS sending one normalization boundary.

I added `src/utils/errors.py` with `IntegrationError`, `CrmError`, and `SmsError`. These errors keep stable `service`, `operation`, `status_code`, and redacted `detail` metadata, plus a `to_dict()` helper for later logs/tests. Sensitive keys such as authorization/token/secret/transcript are scrubbed from surfaced detail, and oversized detail is bounded.

I created provider-agnostic async protocols in `src/services/crm/crm_service.py` and `src/services/alerts/alert_service.py`, plus package `__init__.py` files so S05 can depend on typed CRM and alert behavior without importing concrete GoHighLevel or Twilio implementations yet.

I also recorded D028 in `.gsd/DECISIONS.md` so downstream work knows the shared phone utility returns `None` for unusable inputs and that provider layers are responsible for converting that into typed integration failures when an operation requires a valid number.

## Verification

- Ran `uv run pytest tests/test_types.py tests/test_phone_utils.py`
  - Result: PASS (`63 passed`).
  - Confirms the extended `CallIntakeRecord` defaults and the shared phone-normalization contract.
- Ran a direct import/diagnostic probe:
  - `uv run python - <<'PY' ... from services.crm.crm_service import CrmService; from services.alerts.alert_service import AlertService; from utils.errors import IntegrationError, CrmError, SmsError ... PY`
  - Result: PASS.
  - Confirms the new protocol and error modules import correctly and that `IntegrationError.to_dict()` returns redacted stable metadata.
- Ran `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py`
  - Result: PARTIAL / expected RED remainder.
  - Evidence: collection now advances past the shared utilities and fails only on missing `services.crm.ghl_service` and `services.alerts.sms_service` provider implementations reserved for T03/T04.
- Ran `uv run ruff check src/ tests/`
  - Result: PASS (`All checks passed!`).

## Diagnostics

- Import `normalize_phone` directly from `utils.phone` to inspect the shared normalization boundary.
- Import `IntegrationError`, `CrmError`, or `SmsError` from `utils.errors` and call `.to_dict()` to inspect the redacted diagnostic envelope.
- Import `CrmService` or `AlertService` from `services.crm` / `services.alerts` to inspect the provider-agnostic async protocols S05 should depend on.
- If the full S04 suite still fails at collection, the remaining missing pieces are now localized to `services.crm.ghl_service`, `services.crm.mappers`, and `services.alerts.sms_service` rather than the shared contract layer.

## Deviations

- The written task plan described unusable phone input as raising a stable validation error, but the authoritative RED tests for this slice require `normalize_phone()` to return `None` for invalid or blank input. I implemented the tested contract and documented the downstream provider-responsibility decision in D028.

## Known Issues

- `src/services/crm/ghl_service.py` and `src/services/crm/mappers.py` do not exist yet, so the GoHighLevel tests still fail at import/collection until T03.
- `src/services/alerts/sms_service.py` does not exist yet, so the Twilio tests still fail at import/collection until T04.

## Files Created/Modified

- `src/hvac_types/call_intake_record.py` — added the optional S04 integration fields with backward-compatible defaults.
- `src/utils/__init__.py` — exported the shared phone and error utilities.
- `src/utils/phone.py` — added the shared North American phone normalization helper.
- `src/utils/errors.py` — added typed integration errors with redacted stable metadata and `to_dict()` diagnostics.
- `src/services/__init__.py` — introduced the shared service package root.
- `src/services/crm/__init__.py` — exported the CRM protocol surface.
- `src/services/crm/crm_service.py` — defined the async provider-agnostic CRM protocol.
- `src/services/alerts/__init__.py` — exported the alert protocol surface.
- `src/services/alerts/alert_service.py` — defined the async provider-agnostic alert protocol.
- `.gsd/DECISIONS.md` — appended D028 for the shared phone validation contract.
- `.gsd/milestones/M001/slices/S04/S04-PLAN.md` — marked T02 complete.
