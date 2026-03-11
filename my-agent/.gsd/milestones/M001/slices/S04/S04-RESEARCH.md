# M001/S04 (GoHighLevel CRM and SMS Alert Integrations) — Research

**Date:** 2026-03-11

## Summary

S04 primarily owns **R005 (GoHighLevel CRM Integration)** and **R006 (SMS Owner Alert)**, and directly supports **R004 (background classification output consumption)**, **R008 (config-driven behavior)**, **R009 (graceful failure isolation)**, and **R010 (test coverage)**. The slice can be implemented cleanly as two isolated async services behind protocols: a GoHighLevel service that finds/creates/updates a contact and appends a structured note, and an SMS alert service that sends an owner notification only when the finalized record indicates escalation.

The strongest implementation fit is to standardize on **`httpx.AsyncClient`** for both integrations, even for Twilio, instead of mixing async GHL code with a synchronous Twilio SDK. That aligns with D006 (`httpx` + async client), keeps failure handling uniform, and makes CI payload verification straightforward with `httpx.MockTransport` or `pytest-httpx`. Current code already uses plain dataclasses/enums and thin runtime composition, so S04 should follow the same style: constructor-injected dependencies, no hidden globals, and explicit mapping functions that convert `CallIntakeRecord` into external payloads.

The biggest research finding is that the **current `CallIntakeRecord` contract is not yet rich enough to fully satisfy R005/R006 as written**. It lacks explicit fields for transcript, notify-owner, callback time, and customer type; `summary` may cover AI summary, but the rest are absent. S04 therefore either needs to extend the dataclass now with optional fields or define a temporary note-only strategy that tolerates missing values. The safest path is to extend the record contract with optional fields before wiring the services.

## Recommendation

Implement S04 around four concrete choices:

1. **Use async protocol-backed services**
   - `src/services/crm/crm_service.py`: protocol with `upsert_contact(record)` and `attach_call_note(contact_id, record)`.
   - `src/services/alerts/alert_service.py`: protocol with `send_owner_sms(record)`.
   - `src/services/crm/ghl_service.py` and `src/services/alerts/sms_service.py` should accept injected `httpx.AsyncClient` instances and config/env inputs, not create hidden clients internally.

2. **Use GoHighLevel V2 with Bearer auth + Version header**
   - Base URL: `https://services.leadconnectorhq.com`
   - Required headers seen in official docs: `Authorization: Bearer <token>`, `Version: 2021-07-28`, `Content-Type: application/json`
   - Recommended flow:
     1. normalize caller phone to E.164,
     2. search `GET /contacts/?locationId=...&query=<phone>&limit=10`,
     3. exact-match the returned `contact.phone` after normalization,
     4. `PUT /contacts/{id}` if found, else `POST /contacts/`,
     5. `POST /contacts/{contactId}/notes` with `{"body": ...}`.

3. **Use Twilio REST directly over `httpx`, not `twilio-python`**
   - Twilio docs confirm `POST /2010-04-01/Accounts/{AccountSid}/Messages.json` with **HTTP Basic Auth**.
   - This keeps both integrations async and testable with the same request mocking surface.
   - Send only when a finalized record resolves to `notify_owner=True` (or equivalent derived rule in later slices).

4. **Prefer built-in HTTP mocking first**
   - For this repo, `httpx.MockTransport` is sufficient for payload-shape and failure-isolation tests without adding extra dependencies.
   - `pytest-httpx` is promising if richer request assertions become useful, but it is not required to deliver S04.

## Don’t Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Async REST calls, auth headers, timeouts, error surfaces | `httpx.AsyncClient` + `httpx.Timeout` + `raise_for_status()` | Matches D006, supports async integration work cleanly, and gives a consistent exception surface (`RequestError`, `HTTPStatusError`). |
| Network payload verification in CI | `httpx.MockTransport` (built-in) or `pytest-httpx` | Lets tests assert URL/method/headers/body exactly without real GoHighLevel/Twilio credentials or flaky live network calls. |
| Twilio HTTP auth | Twilio REST contract (Basic Auth to `Messages.json`) | Avoids inventing a custom SMS transport and keeps the implementation lightweight without a sync SDK. |

## Existing Code and Patterns

- `src/hvac_types/call_intake_record.py` — Current downstream contract for CRM/SMS work. Reuse it as the central mapper input, but note it is currently missing several R005/R006 fields (`transcript`, `notify_owner`, `callback_time`, `customer_type`).
- `src/hvac_types/classification.py` — Reuse `IssueCategory`, `UrgencyLevel`, and `DangerType` directly in CRM note formatting and SMS text; enum `__str__` behavior is already hardened for Python 3.13.
- `src/config/load_config.py` — Current validation boundary only enforces `business_name`, `timezone`, and `owner_phone`. Integration secrets are not yet validated anywhere, so S04 should introduce explicit service/factory validation for required env vars.
- `src/config/hvac_demo_config.py` — `owner_phone` already lives in business config; S04 should use that as the alert destination rather than inventing a separate owner-recipient setting.
- `src/conversation/intake_task.py` — Current phone extraction returns `416-555-0199` style values, not E.164. S04 must normalize before contacting GoHighLevel or Twilio to avoid duplicate contacts and Twilio 400s.
- `src/classification/live_classifier.py` — S04 consumes these classifications indirectly through the finalized record; do not reclassify in the integration layer.
- `tests/test_intake_task.py` / `tests/test_conversation_controller.py` — The existing suite favors focused pytest tests with inspectable state and no broad end-to-end network coupling. S04 tests should follow that pattern.
- `src/agent_starter_python.egg-info/requires.txt` — The checked-in metadata currently lists only LiveKit and dotenv. `httpx` is importable in the current environment, but it is not declared here; dependency declaration/update work is likely needed during implementation.

## Constraints

- S04 owns **R005** and **R006** and must also support **R009**: CRM failure must not crash the voice session, and SMS failure must not block CRM.
- D006 explicitly chose **`httpx` with async client** for integrations.
- D007 chose **Twilio as the default SMS provider**, but behind an abstraction.
- S04 produces modules under `src/services/...` and `src/utils/...`; imports in the repo are rooted from `src/` (for example `from hvac_types...`), so new packages should follow the same absolute-import pattern.
- Business-specific values belong in config; secrets must remain environment-driven. Current codebase has no integration-secret validation yet.
- The repo snapshot does **not** currently include a visible `pyproject.toml` or `.env.example`, despite milestone context expecting them. Implementation may need to locate or recreate the dependency/env manifest path before shipping.

## Common Pitfalls

- **GoHighLevel field-name ambiguity** — Context7 surfaced both camelCase (`firstName`, `lastName`, `address1`) and snake_case examples from different doc sources. Prefer the higher-confidence V2 contact examples using **camelCase** plus `locationId`; do not mix naming styles in one payload.
- **Assuming GoHighLevel has a true contact upsert endpoint** — The docs we found show create/search/update, not a dedicated phone upsert. Implement upsert as search-by-phone + exact normalized phone match + create/update.
- **Using raw extracted phone strings directly** — The conversation layer emits dashed local numbers, which will fragment GHL contact matching and can fail Twilio sends. Normalize once in `src/utils/phone.py` and use that everywhere.
- **Overcoupling CRM and SMS** — R009 requires SMS failure isolation. The CRM service should complete independently even when alert delivery fails.
- **Treating GoHighLevel notes as structured JSON fields** — The notes endpoint expects a plain `body` string. Structured fields, summary, and transcript should be rendered into a deterministic text block instead of assuming nested JSON note metadata.
- **Pulling in the synchronous Twilio Python client by default** — It works, but it conflicts with the project’s async integration choice and adds a second transport/testing surface for little benefit in this slice.

## Open Risks

- **`CallIntakeRecord` is under-specified for this slice** — Missing fields could force either premature type churn in S04 or awkward temporary note formatting that leaves R005/R006 only partially satisfied.
- **GoHighLevel duplicate matching may be fuzzy** — The docs show `query=` search, but not an exact phone lookup contract. Exact matching will need defensive filtering of returned contacts.
- **Unknown env contract for GHL credentials** — Twilio env names are straightforward (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`), but GoHighLevel naming is still a project decision. Recommended names: `GHL_API_TOKEN`, `GHL_LOCATION_ID`, optional `GHL_API_VERSION`, optional `GHL_BASE_URL`.
- **No visible dependency manifest in this workspace snapshot** — Even though `httpx` imports today, dependency pinning and future CI reproducibility may fail unless the actual manifest is updated during implementation.
- **Need user-pasted external proof if deeper GHL behavior matters** — We have enough official Context7-backed material for endpoints/headers/notes body, but not for stronger guarantees around exact duplicate lookup semantics.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LiveKit Agents | `livekit-agents` | installed |
| GoHighLevel | none found via `npx skills find "GoHighLevel"` | none found |
| Twilio | `sickn33/antigravity-awesome-skills@twilio-communications` | available — best result found (360 installs). Install: `npx skills add sickn33/antigravity-awesome-skills@twilio-communications` |
| HTTPX | `slanycukr/riot-api-project@httpx` | available but low-confidence/relevance (22 installs). Install: `npx skills add slanycukr/riot-api-project@httpx` |

## Sources

- GoHighLevel V2 contact create/search/update requires Bearer auth and a `Version` header; contact create examples use camelCase fields and `locationId`. (source: [HighLevel API Docs — Contacts API](https://github.com/gohighlevel/highlevel-api-docs))
- GoHighLevel contact notes are created at `POST /contacts/{contactId}/notes` with a request body containing `body` text. (source: [HighLevel API Docs — Contact Notes API](https://github.com/gohighlevel/highlevel-api-docs))
- Twilio messaging requests can be sent via `POST /2010-04-01/Accounts/{AccountSid}/Messages.json` using HTTP Basic Authentication. (source: [Twilio Docs — API Authentication / Messaging](https://www.twilio.com/docs/messaging))
- `httpx.AsyncClient`, `Timeout`, `raise_for_status()`, `RequestError`, `HTTPStatusError`, and `MockTransport` provide the right async/test surface for integration services. (source: [HTTPX Docs](https://github.com/encode/httpx))
- `pytest-httpx` can capture and assert outgoing HTTPX requests if richer test ergonomics are later desired. (source: [pytest-httpx](https://github.com/Colin-b/pytest_httpx))
