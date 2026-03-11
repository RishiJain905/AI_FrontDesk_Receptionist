# S04: GoHighLevel CRM and SMS Alert Integrations

**Goal:** Add production-oriented GoHighLevel and SMS integration boundaries that can turn a finalized `CallIntakeRecord` into an external CRM write plus an owner alert without coupling either service to the voice session runtime.
**Demo:** In mocked async service tests, a finalized HVAC intake record is normalized once, upserted into GoHighLevel by phone, annotated with a deterministic structured note containing transcript and AI summary, and converted into a concise Twilio SMS only when `notify_owner` is true, with CRM and SMS failures surfacing as separate typed errors.

## Must-Haves

- `CallIntakeRecord` grows the optional integration fields S04 needs (`callback_time`, `customer_type`, `transcript`, `ai_summary`, `notify_owner`, `sms_sent`) without breaking existing callers.
- `normalize_phone(number)` becomes the single path used by both GoHighLevel and Twilio so duplicate-contact matching and outbound SMS formatting are consistent.
- `GoHighLevelService` implements search-by-phone → exact normalized match → create/update contact → attach note using GoHighLevel v2 Bearer auth plus the required `Version` header.
- GoHighLevel note formatting preserves the existing classification outputs (`issue_category`, `urgency_level`, `danger_type`) and includes callback time, customer type, transcript, and AI summary in deterministic text form.
- `TwilioSmsService` sends a concise owner alert only when `notify_owner` is true and `sms_sent` is still false, using direct async HTTP with Basic Auth instead of a sync SDK.
- CRM and SMS failure surfaces stay isolated via protocols and typed integration errors so S05 can continue CRM/SMS orchestration without one service importing or blocking the other.
- Slice verification proves owned requirements R005 and R006 at the service boundary and also checks failure diagnostics that support R009.

## Proof Level

- This slice proves: integration
- Real runtime required: no
- Human/UAT required: no

## Verification

- `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py`
- `uv run ruff check src/ tests/`

## Observability / Diagnostics

- Runtime signals: typed `IntegrationError`, `CrmError`, and `SmsError` surfaces carry stable service/operation/status metadata; deterministic mapper output keeps request and note formatting directly assertable in tests.
- Inspection surfaces: `tests/test_ghl_service.py`, `tests/test_sms_service.py`, `tests/test_phone_utils.py`, and `tests/test_types.py`; direct imports of `normalize_phone()`, CRM mapper helpers, and service return values/errors.
- Failure visibility: search/create/update/note/send failures expose which operation failed and the HTTP status without requiring raw credential dumps or unbounded payload logging.
- Redaction constraints: auth tokens, Twilio credentials, and full transcript/PII must not be emitted in exception messages or diagnostics beyond the bounded request/operation context needed to localize the failure.

## Integration Closure

- Upstream surfaces consumed: `src/hvac_types/call_intake_record.py`, `src/hvac_types/business_config.py`, `src/hvac_types/classification.py`, `src/config/load_config.py`, and the classification outputs already produced by S02/S03.
- New wiring introduced in this slice: `src/services/crm/` service + mappers, `src/services/alerts/` service, shared `src/utils/phone.py` and `src/utils/errors.py`, and the protocol boundary S05 will call during finalization.
- What remains before the milestone is truly usable end-to-end: S05 must assemble transcripts/final summaries at runtime, decide partial vs complete finalization, call the services from the lifecycle, and perform real-credential operational proof/UAT.

## Tasks

- [x] **T01: Lock the S04 boundary with failing CRM, SMS, and phone-normalization tests** `est:50m`
  - Why: The slice needs an explicit RED stopping condition before new integration code lands, otherwise it is easy to ship mapper or payload assumptions that do not actually prove R005/R006.
  - Files: `tests/test_ghl_service.py`, `tests/test_sms_service.py`, `tests/test_phone_utils.py`, `tests/test_types.py`
  - Do: Add pytest coverage that names the planned S04 modules directly, asserts the new `CallIntakeRecord` fields, verifies `normalize_phone()` behavior, and uses `httpx.MockTransport` expectations for GoHighLevel search/create/update/note requests plus Twilio send/skip/error flows. Include at least one assertion on typed error metadata so the failure-path diagnostic contract is defined before implementation.
  - Verify: `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py`
  - Done when: The named tests exist, collect successfully, and fail only because the S04 runtime modules/fields are not implemented yet.
- [x] **T02: Extend the integration-facing record contract and shared utilities** `est:1h`
  - Why: S04 cannot format correct CRM notes or SMS payloads until the call record exposes the needed fields and both services share the same phone/error utility boundary.
  - Files: `src/hvac_types/call_intake_record.py`, `src/utils/phone.py`, `src/utils/errors.py`, `src/services/crm/crm_service.py`, `src/services/alerts/alert_service.py`, `tests/test_types.py`, `tests/test_phone_utils.py`
  - Do: Add the missing optional record fields without breaking existing defaults, create `normalize_phone()` for the North American numbers emitted by intake, define typed integration errors with stable service/operation/status surfaces and redacted messages, and introduce async CRM/alert protocols that S05 can depend on without knowing the concrete provider.
  - Verify: `uv run pytest tests/test_types.py tests/test_phone_utils.py`
  - Done when: The record/utility/protocol tests pass and the S04 test suite can import the shared contracts it needs.
- [x] **T03: Implement GoHighLevel contact upsert and structured note mapping** `est:1h15m`
  - Why: R005 is the core product output for this slice; without the real search/create/update/note flow the CRM write path is still only aspirational.
  - Files: `src/services/crm/mappers.py`, `src/services/crm/ghl_service.py`, `src/services/crm/__init__.py`, `tests/test_ghl_service.py`
  - Do: Build deterministic contact/note mappers from `CallIntakeRecord`, implement `GoHighLevelService` with injected `httpx.AsyncClient`, set Bearer + `Version` headers, normalize phone search input, exact-match returned phones before deciding create vs update, post the structured note, and raise `CrmError` with operation/status context on request or HTTP failures.
  - Verify: `uv run pytest tests/test_ghl_service.py tests/test_phone_utils.py`
  - Done when: The CRM tests prove create, update, note attachment, and typed failure diagnostics against `httpx.MockTransport`.
- [x] **T04: Implement Twilio owner alerts and close the slice verification gate** `est:1h`
  - Why: R006 is the second owned requirement, and the slice is not done until the alert path is real, skip-aware, and demonstrably isolated from CRM internals.
  - Files: `src/services/alerts/sms_service.py`, `src/services/alerts/__init__.py`, `tests/test_sms_service.py`, `src/services/alerts/alert_service.py`
  - Do: Format concise owner-alert text from the finalized record, skip sends when `notify_owner` is false or `sms_sent` is already true, send Twilio `Messages.json` requests via Basic Auth on an injected `httpx.AsyncClient`, normalize numbers consistently, raise `SmsError` with operation/status metadata on failures, and finish by running the full S04 verification plus Ruff.
  - Verify: `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py && uv run ruff check src/ tests/`
  - Done when: SMS send/skip/error tests pass, the full slice verification is green, and the SMS provider remains isolated behind the alert protocol boundary.

## Files Likely Touched

- `src/hvac_types/call_intake_record.py`
- `src/utils/phone.py`
- `src/utils/errors.py`
- `src/services/crm/crm_service.py`
- `src/services/crm/mappers.py`
- `src/services/crm/ghl_service.py`
- `src/services/alerts/alert_service.py`
- `src/services/alerts/sms_service.py`
- `tests/test_ghl_service.py`
- `tests/test_sms_service.py`
- `tests/test_phone_utils.py`
- `tests/test_types.py`
