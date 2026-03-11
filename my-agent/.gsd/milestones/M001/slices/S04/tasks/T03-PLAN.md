---
estimated_steps: 5
estimated_files: 4
---

# T03: Implement GoHighLevel contact upsert and structured note mapping

**Slice:** S04 — GoHighLevel CRM and SMS Alert Integrations
**Milestone:** M001

## Description

Implement the real GoHighLevel provider using the shared S04 contracts. This task closes the main CRM delivery path for R005 by turning a finalized call record into a contact create/update plus a structured note attachment using the documented v2 API flow.

## Steps

1. Add `src/services/crm/mappers.py` with deterministic `to_ghl_contact(record, location_id)` and `to_ghl_note(record)` helpers that preserve classification outputs and render transcript/AI summary as structured note text.
2. Add `src/services/crm/ghl_service.py` implementing `GoHighLevelService` with constructor-injected `httpx.AsyncClient`, base URL, API token, location ID, and API version defaults.
3. Implement the documented upsert flow: normalize the caller phone, search contacts with `GET /contacts/`, exact-match returned phones after normalization, `POST /contacts/` when absent or `PUT /contacts/{id}` when present, then `POST /contacts/{contactId}/notes`.
4. Wrap `httpx` request and status failures in `CrmError` with operation-specific metadata and without leaking bearer tokens or oversized raw response bodies.
5. Run the CRM-specific test suite until the create/update/note and failure-diagnostic expectations all pass.

## Must-Haves

- [ ] GoHighLevel request headers include Bearer auth, `Version`, and JSON content type using the documented v2 base URL shape.
- [ ] Contact upsert decisions are driven by exact normalized phone comparison, not by trusting fuzzy search results blindly.
- [ ] The note body is deterministic text that includes urgency, issue category, danger, callback time, customer type, transcript, and AI summary when present.
- [ ] CRM failures surface `CrmError` with enough metadata for S05 retry/logging without forcing downstream code to parse raw `httpx` exceptions.

## Verification

- `uv run pytest tests/test_ghl_service.py tests/test_phone_utils.py`
- Expected result: PASS, proving the mocked GoHighLevel provider performs the documented request flow and exposes stable diagnostics.

## Observability Impact

- Signals added/changed: CRM operations become inspectable as discrete phases (`search_contact`, `create_contact`, `update_contact`, `attach_call_note`) through typed errors and deterministic mapper output.
- How a future agent inspects this: Run `tests/test_ghl_service.py` or instantiate `GoHighLevelService` with `httpx.MockTransport` to inspect outbound request order and payloads.
- Failure state exposed: Which CRM phase failed, at what HTTP status, and with which non-secret request context becomes visible without live-network guessing.

## Inputs

- `src/services/crm/crm_service.py` — protocol boundary from T02.
- `src/utils/phone.py` and `src/utils/errors.py` — shared normalization and error surfaces.
- `tests/test_ghl_service.py` — RED CRM contract from T01.
- S04 research summary — required GoHighLevel headers, endpoint sequence, and note body contract.

## Expected Output

- `src/services/crm/mappers.py` — deterministic GoHighLevel contact and note payload builders.
- `src/services/crm/ghl_service.py` — async GoHighLevel provider implementing the S04 CRM contract.
- `src/services/crm/__init__.py` — exports for provider + mapper surfaces used by later slices/tests.
