---
id: T03
parent: S04
milestone: M001
provides:
  - Real GoHighLevel CRM provider with deterministic contact/note mapping, exact normalized-phone upsert decisions, and typed phase-specific CRM failures
key_files:
  - src/services/crm/ghl_service.py
  - src/services/crm/mappers.py
  - src/services/crm/__init__.py
  - tests/test_ghl_service.py
key_decisions:
  - D029: GoHighLevel search results are treated as candidates only; create vs update is decided by exact shared-phone normalization equality
patterns_established:
  - Provider implementations should use shared normalization at the decision boundary, deterministic mapper helpers for payload proof, and typed operation-scoped errors for retry/logging
observability_surfaces:
  - CrmError(service='gohighlevel', operation, status_code, detail); tests/test_ghl_service.py; mapper helpers in services.crm.mappers
duration: 55m
verification_result: passed
completed_at: 2026-03-11T18:29:16-04:00
blocker_discovered: false
---

# T03: Implement GoHighLevel contact upsert and structured note mapping

**Added the real GoHighLevel contact search/create/update/note flow with deterministic payload builders and stable CRM diagnostics.**

## What Happened

Implemented `src/services/crm/mappers.py` with deterministic contact and note builders, plus slice-plan aliases (`to_ghl_contact`, `to_ghl_note`) and the test-facing names (`build_contact_payload`, `build_contact_note`). The note mapper renders a stable ordered text body covering call status, classification outputs, callback metadata, summary, transcript, and AI summary when present.

Implemented `src/services/crm/ghl_service.py` as the concrete async CRM provider. It injects `httpx.AsyncClient`, uses the GoHighLevel v2 base URL, sends Bearer auth plus `Version`/JSON headers, normalizes the caller phone once, searches `/contacts/`, exact-matches returned phones only after shared normalization, creates or updates the contact accordingly, and attaches the structured note via `/contacts/{contactId}/notes`.

Wrapped request and HTTP failures in `CrmError` with `service='gohighlevel'`, phase-specific `operation` values (`normalize_phone`, `search_contact`, `create_contact`, `update_contact`, `attach_call_note`), HTTP status when present, and bounded non-secret detail. Also exported the provider and mapper surfaces from `src/services/crm/__init__.py`.

To harden the RED contract, added one extra CRM test proving that fuzzy search results with non-matching phones still trigger contact creation rather than blindly updating the returned record.

## Verification

Ran task verification:

- `uv run pytest tests/test_ghl_service.py tests/test_phone_utils.py` → PASS (`18 passed`)

Ran slice-level checks required at this stage:

- `uv run pytest tests/test_ghl_service.py tests/test_sms_service.py tests/test_phone_utils.py tests/test_types.py` → expected partial failure at collection because `services.alerts.sms_service` is still unimplemented for T04
- `uv run ruff check src/ tests/` → PASS

Behavior confirmed by tests includes deterministic mapper output, correct request order for create/update flows, exact normalized-phone matching, note attachment, and typed `CrmError` metadata on HTTP failures.

## Diagnostics

Future inspection paths:

- Run `uv run pytest tests/test_ghl_service.py` to inspect GoHighLevel request order, payload shapes, and error-surface expectations.
- Import `build_contact_payload()` / `build_contact_note()` from `services.crm.mappers` to inspect deterministic outbound mapping directly.
- Instantiate `GoHighLevelService` with `httpx.MockTransport` and inspect `CrmError.to_dict()` for stable `service` / `operation` / `status_code` diagnostics.

## Deviations

- Added one extra CRM regression test (`test_upsert_contact_creates_new_contact_when_search_returns_only_non_matching_phones`) beyond the written task plan to lock the exact-match duplicate rule explicitly.

## Known Issues

- Full S04 verification still stops at `tests/test_sms_service.py` collection because `src/services/alerts/sms_service.py` remains for T04.

## Files Created/Modified

- `src/services/crm/mappers.py` — deterministic GoHighLevel contact and note payload builders
- `src/services/crm/ghl_service.py` — async GoHighLevel provider with search/create/update/note flow and typed CRM error wrapping
- `src/services/crm/__init__.py` — exports for CRM protocol, provider, and mapper helpers
- `tests/test_ghl_service.py` — added a regression test proving fuzzy search results do not bypass exact normalized-phone matching
- `.gsd/milestones/M001/slices/S04/S04-PLAN.md` — marked T03 complete
- `.gsd/DECISIONS.md` — recorded the exact normalized-phone duplicate-match rule as D029
