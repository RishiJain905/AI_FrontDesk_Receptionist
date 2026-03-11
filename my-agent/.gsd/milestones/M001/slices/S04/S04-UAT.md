# S04: GoHighLevel CRM and SMS Alert Integrations — UAT

**Milestone:** M001
**Written:** 2026-03-11

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S04 is an integration-boundary slice, so the most trustworthy proof is deterministic executable verification of payload shape, request order, skip behavior, and typed failure diagnostics against mock HTTP transports rather than a flaky external-network demo.

## Preconditions

- Project dependencies are installed via `uv`.
- `src/services/crm/ghl_service.py`, `src/services/crm/mappers.py`, `src/services/alerts/sms_service.py`, `src/utils/phone.py`, and `src/utils/errors.py` are present.
- The repository root is the current working directory.
- No live GoHighLevel or Twilio credentials are required for this UAT.

## Smoke Test

Run:

- `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py -q`

Passing this command confirms the shared phone/error contract exists, the finalized record shape includes the S04 integration fields, and both provider boundaries satisfy their executable request-shape tests.

## Test Cases

### 1. GoHighLevel create path writes a deterministic contact and note

1. Run `uv run pytest tests/test_ghl_service.py -q`.
2. Inspect the passing case `test_upsert_contact_creates_new_contact_and_attaches_note_when_no_exact_match_exists`.
3. **Expected:** The provider performs `GET /contacts/` with the normalized phone, then `POST /contacts/`, then `POST /contacts/{contactId}/notes`, using Bearer auth plus the `Version` header and the deterministic note body.

### 2. GoHighLevel update path only trusts exact normalized-phone matches

1. Run `uv run pytest tests/test_ghl_service.py -q`.
2. Inspect the passing cases `test_upsert_contact_updates_exact_phone_match_then_attaches_note` and `test_upsert_contact_creates_new_contact_when_search_returns_only_non_matching_phones`.
3. **Expected:** A returned contact is updated only when its phone normalizes to the exact caller number; fuzzy non-matching search results still lead to a fresh contact create.

### 3. Twilio owner alert sends only when escalation is enabled

1. Run `uv run pytest tests/test_sms_service.py -q`.
2. Inspect the passing cases `test_send_owner_alert_posts_twilio_form_request_with_basic_auth` and `test_send_owner_alert_skips_outbound_request_when_notification_is_disabled_or_already_sent`.
3. **Expected:** The provider posts exactly one Twilio `Messages.json` form request with Basic Auth when `notify_owner=True` and `sms_sent=False`, but performs no outbound request when alerts are disabled or already sent.

### 4. Typed diagnostics stay actionable and redacted

1. Run `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py -q`.
2. Run `uv run python - <<'PY' ... from utils.errors import CrmError, SmsError ... print(error.to_dict()) ... PY` with synthetic data.
3. **Expected:** Provider failures surface stable `service`, `operation`, and `status_code` metadata, while secrets and transcript content are redacted from surfaced detail.

## Edge Cases

### Invalid or blank phone input is rejected at the provider boundary

1. Run `uv run pytest tests/test_phone_utils.py -q`.
2. Confirm `normalize_phone()` returns `None` for blank/invalid input.
3. Inspect the provider code paths for `operation="normalize_phone"` failures.
4. **Expected:** Shared normalization stays reusable and side-effect free, while provider layers convert invalid-required numbers into typed CRM/SMS failures when a request cannot proceed.

## Failure Signals

- `ModuleNotFoundError` for `services.crm.*`, `services.alerts.*`, or `utils.*`
- `test_upsert_contact_creates_new_contact_when_search_returns_only_non_matching_phones` fails because a fuzzy GoHighLevel search result is updated incorrectly
- `test_send_owner_alert_posts_twilio_form_request_with_basic_auth` fails because the request is not a Twilio form post, lacks Basic Auth, or uses non-normalized numbers
- `CrmError` / `SmsError` messages expose raw tokens, transcripts, or oversized payload content
- `test_send_owner_alert_skips_outbound_request_when_notification_is_disabled_or_already_sent` fails because an outbound request still occurs

## Requirements Proved By This UAT

- R005 — Proves finalized call records can be deterministically mapped into GoHighLevel search/create/update/note requests with exact normalized-phone duplicate control and typed CRM failure diagnostics.
- R006 — Proves owner alerts are formatted concisely, sent only when escalation is enabled, skipped when already sent/disabled, and surfaced through typed SMS failure diagnostics.

## Not Proven By This UAT

- R005 live operational proof with real GoHighLevel credentials and an observed contact record is not proven by this UAT.
- R006 live operational proof with real Twilio credentials and an actual delivered SMS is not proven by this UAT.
- R009 full lifecycle isolation is not proven here because S05 still has to wire CRM and SMS into post-call orchestration and partial-call finalization.
- Human phone-call experience through LiveKit console or SIP is not exercised here.

## Notes for Tester

This UAT intentionally validates the slice at the service boundary rather than through external-network calls. If the CRM tests fail, inspect `src/services/crm/ghl_service.py` and `src/services/crm/mappers.py` first. If the SMS tests fail, inspect `src/services/alerts/sms_service.py`. If diagnostic assertions fail, inspect `src/utils/errors.py` and ensure provider code is not bypassing the shared redaction surface.
