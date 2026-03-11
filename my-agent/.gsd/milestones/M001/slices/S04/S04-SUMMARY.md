---
id: S04
parent: M001
milestone: M001
provides:
  - Provider-backed GoHighLevel CRM and Twilio SMS service boundaries, shared phone/error utilities, deterministic payload mappers, and executable integration proof for finalized call records
requires:
  - slice: S01
    provides: `CallIntakeRecord` and `BusinessConfig` types that now carry the finalized-call fields consumed by CRM and SMS integrations
affects:
  - S05
key_files:
  - src/hvac_types/call_intake_record.py
  - src/utils/phone.py
  - src/utils/errors.py
  - src/services/crm/ghl_service.py
  - src/services/crm/mappers.py
  - src/services/alerts/sms_service.py
  - tests/test_ghl_service.py
  - tests/test_sms_service.py
key_decisions:
  - S04 proof uses `httpx.MockTransport` tests to lock exact request shapes and typed integration diagnostics before any live-credential proof
  - `normalize_phone()` is the single shared normalization path; invalid-required numbers are converted into provider-specific typed failures at the CRM/SMS boundary
  - GoHighLevel search results are candidates only; exact normalized-phone equality decides create vs update
  - Twilio skip/send logic and duplicate-prevention checks live inside `TwilioSmsService`, not in downstream orchestration
patterns_established:
  - External integrations stay behind provider-agnostic async protocols so lifecycle orchestration can call CRM and SMS independently
  - Deterministic mapper/message helpers make outbound payloads directly assertable in tests and easier to diagnose in retries
  - Typed `CrmError` / `SmsError` surfaces expose stable `service` / `operation` / `status_code` metadata while redacting secrets and transcript content
observability_surfaces:
  - `tests/test_ghl_service.py`, `tests/test_sms_service.py`, `tests/test_phone_utils.py`, and `tests/test_types.py`
  - `utils.errors.IntegrationError.to_dict()` plus stable exception attributes on `CrmError` and `SmsError`
  - `services.crm.mappers.build_contact_payload()` / `build_contact_note()` and `services.alerts.sms_service.build_owner_alert_text()`
  - `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py`
  - `uv run ruff check src/ tests/`
  - `uv run python - <<'PY' ... from utils.errors import CrmError, SmsError ... print(error.to_dict()) ... PY`
drill_down_paths:
  - .gsd/milestones/M001/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S04/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S04/tasks/T03-SUMMARY.md
  - .gsd/milestones/M001/slices/S04/tasks/T04-SUMMARY.md
duration: 2h27m
verification_result: passed
completed_at: 2026-03-11T18:29:00-04:00
---

# S04: GoHighLevel CRM and SMS Alert Integrations

**Shipped the real S04 integration boundary: finalized HVAC call records now map deterministically into GoHighLevel contact/note writes and concise Twilio owner alerts behind isolated async service protocols with typed, redacted failure diagnostics.**

## What Happened

T01 locked the slice boundary with RED tests that imported the planned `services.*` and `utils.*` modules directly, extended `CallIntakeRecord` with the new integration-facing fields, and defined the exact proof surfaces for CRM request order, note formatting, SMS skip/send behavior, shared phone normalization, and typed error metadata.

T02 turned that contract into shared infrastructure. `CallIntakeRecord` gained `callback_time`, `customer_type`, `transcript`, `ai_summary`, `notify_owner`, and `sms_sent` without breaking earlier slices. `src/utils/phone.py` became the single normalization path for CRM matching and Twilio delivery, `src/utils/errors.py` introduced redacted typed integration errors with stable metadata, and provider-agnostic `CrmService` / `AlertService` protocols gave S05 clean orchestration seams.

T03 implemented the real GoHighLevel provider. `src/services/crm/mappers.py` now renders deterministic contact payloads and structured CRM notes that preserve call status, classification outputs, callback metadata, transcript, and AI summary in a stable order. `GoHighLevelService` performs the full search-by-phone → exact normalized match → create/update → note-attach flow with GoHighLevel v2 headers and raises phase-specific `CrmError` instances when normalization, transport, JSON parsing, or HTTP status handling fails.

T04 implemented the real Twilio provider and closed the slice gate. `TwilioSmsService` now normalizes sender/owner numbers, skips outbound work when `notify_owner` is false or `sms_sent` is already true, posts `Messages.json` requests with Basic Auth using async `httpx`, formats concise owner alerts from the finalized record, and raises typed `SmsError` diagnostics without leaking auth material. The full S04 test and Ruff gates then passed cleanly.

## Verification

Fresh completion verification:

- `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py` — PASS (`74 passed`)
- `uv run ruff check src/ tests/` — PASS (`All checks passed!`)
- `uv run python - <<'PY' ... from utils.errors import CrmError, SmsError ... print(error.to_dict()) ... PY` — PASS; confirmed externally visible, redacted `service` / `operation` / `status_code` diagnostics and that secrets/transcript fields are scrubbed from surfaced detail

What this proves now:

- GoHighLevel contact payloads and notes are deterministic and directly assertable
- GoHighLevel create vs update decisions depend on exact shared-phone normalization rather than fuzzy search results
- Twilio alert formatting, Basic Auth request shape, and send/skip rules are locked by executable tests
- CRM and SMS failures surface independently through typed provider-specific errors with actionable, non-secret metadata

## Requirements Advanced

- R004 — S04 preserves the classification outputs from earlier slices by carrying issue category, urgency, and danger data through deterministic CRM notes and SMS fallback formatting.
- R005 — Added the real GoHighLevel search/create/update/note provider boundary that finalized call records can use in S05.
- R006 — Added the real Twilio owner-alert provider boundary with concise message formatting and duplicate-prevention skip rules.
- R009 — Added the typed, redacted CRM/SMS error surfaces and protocol isolation that S05 will rely on for graceful failure handling.
- R010 — Added executable pytest coverage for CRM payloads, Twilio request shape, phone normalization, and typed failure diagnostics.

## Requirements Validated

- R005 — `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py` now proves deterministic GoHighLevel contact mapping, exact normalized-phone create/update selection, structured note attachment, and typed CRM failure diagnostics via mock HTTP transport.
- R006 — `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py` now proves concise owner-alert formatting, notify_owner/sms_sent skip behavior, Twilio Basic Auth form-post request shape, and typed SMS failure diagnostics via mock HTTP transport.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- The plan text suggested provider layers might raise validation errors from the shared phone utility boundary, but the authoritative RED tests required `normalize_phone()` to return `None` for invalid input. S04 implemented the tested contract and moved provider-specific failure conversion into `GoHighLevelService` and `TwilioSmsService`.
- Added one extra regression test for the GoHighLevel fuzzy-search edge case to ensure non-matching returned contacts never bypass the exact normalized-phone duplicate rule.

## Known Limitations

- This slice proves the integration boundary with mocked async HTTP, not live GoHighLevel or Twilio credentials. Real operational proof remains for S05/S06 milestone completion work.
- S04 does not yet orchestrate partial vs complete call finalization, transcript assembly, post-call summary generation, or actual retry/logging behavior inside the lifecycle; S05 must wire these providers into the call flow.
- `sms_sent` duplicate-prevention state exists on the record and inside the provider skip rule, but S05 still needs to persist/update that flag during finalization.

## Follow-ups

- S05 should call CRM and SMS via the protocol boundaries independently so one provider failure cannot block the other.
- S05 should use `IntegrationError.to_dict()` / `CrmError.to_dict()` / `SmsError.to_dict()` for structured retry/logging rather than inventing new ad hoc error formatting.
- S05 should finalize transcripts and AI summaries before invoking `build_contact_note()` / `build_owner_alert_text()` so the deterministic outbound text surfaces stay useful.

## Files Created/Modified

- `src/hvac_types/call_intake_record.py` — extended the finalized-call contract with the S04 integration fields
- `src/utils/phone.py` — added the shared North American phone normalization helper used by both providers
- `src/utils/errors.py` — added stable, redacted typed integration errors and `to_dict()` diagnostics
- `src/services/crm/crm_service.py` — defined the provider-agnostic async CRM protocol for downstream orchestration
- `src/services/crm/mappers.py` — added deterministic GoHighLevel contact and note builders
- `src/services/crm/ghl_service.py` — implemented the async GoHighLevel v2 search/create/update/note flow with typed failures
- `src/services/alerts/alert_service.py` — defined the provider-agnostic async alert protocol
- `src/services/alerts/sms_service.py` — implemented the async Twilio send/skip/error boundary and concise owner-alert formatter
- `src/services/crm/__init__.py` — exported the CRM protocol, provider, and mapper helpers
- `src/services/alerts/__init__.py` — exported the alert protocol, Twilio provider, and alert formatter
- `tests/test_ghl_service.py` — added executable proof for GoHighLevel mapper output, request order, exact-match updates, and typed failures
- `tests/test_sms_service.py` — added executable proof for Twilio message formatting, send/skip behavior, Basic Auth request shape, and typed failures
- `tests/test_phone_utils.py` — added executable proof for the shared normalization boundary
- `tests/test_types.py` — locked the extended `CallIntakeRecord` integration-field contract
- `.gsd/REQUIREMENTS.md` — recorded validation evidence for R005 and R006 and updated the validated-count summary
- `.gsd/milestones/M001/M001-ROADMAP.md` — marked S04 complete
- `.gsd/PROJECT.md` — refreshed project state to reflect S04 completion and the remaining S05-S06 work
- `.gsd/STATE.md` — advanced active-state tracking to show S04 complete and S05 next

## Forward Intelligence

### What the next slice should know
- The clean S05 seam is the protocol layer (`CrmService` and `AlertService`), not the concrete GoHighLevel/Twilio classes directly; keep lifecycle orchestration provider-agnostic.
- `build_contact_note()` and `build_owner_alert_text()` are already deterministic and test-proven, so S05 should feed them finalized record fields rather than reformatting outbound text in the lifecycle.
- Exact phone normalization is doing real product work now: it controls GoHighLevel duplicate detection and Twilio delivery addressing, so do not fork or bypass `normalize_phone()` downstream.

### What's fragile
- GoHighLevel note/contact payload assumptions — they are locked by tests, but live API payload drift or undocumented field changes would surface only once real credentials are exercised.
- SMS duplicate-prevention semantics — provider-level skip behavior is correct, but lifecycle state must still update `sms_sent` reliably after a successful send to avoid repeats across retries.

### Authoritative diagnostics
- `tests/test_ghl_service.py` — best source for the exact GoHighLevel request order, headers, payload shapes, and error-surface expectations
- `tests/test_sms_service.py` — best source for Twilio send/skip behavior, Basic Auth form-post shape, and typed failure expectations
- `utils.errors.IntegrationError.to_dict()` — best runtime diagnostic surface for structured, redacted provider failures without leaking credentials or transcript content

### What assumptions changed
- "GoHighLevel search results can be trusted directly" — false; S04 proved the search endpoint must be treated as fuzzy and resolved with exact normalized-phone matching before update.
- "Phone validation belongs entirely in a shared utility exception" — false for this slice; the tested contract is `normalize_phone() -> str | None`, with provider boundaries responsible for escalating invalid-required input into typed CRM/SMS failures.
