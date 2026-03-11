# GSD State

**Active Milestone:** M001 — HVAC After-Hours Voice Agent
**Active Slice:** None (S04 complete; S05 next)
**Active Task:** None
**Phase:** S04 is complete and verified. The codebase now has provider-backed GoHighLevel CRM and Twilio SMS boundaries, shared phone/error utilities, deterministic CRM note/contact mapping, and executable service-boundary proof for R005/R006.

## Recent Decisions

- D006: `httpx` async client remains the integration transport choice for external REST work.
- D011: Duplicate alert prevention stays on `sms_sent` state tracked with the call record/lifecycle.
- D012: GoHighLevel integration targets the v2 API at `https://services.leadconnectorhq.com`.
- D025: S04 proof uses `httpx.MockTransport` request-shape tests plus typed failure diagnostics; live credential proof stays for later operational/UAT work.
- D026: Integration failures must surface stable `service` / `operation` / `status_code` metadata while redacting secrets and oversized transcript payloads.
- D027: `CallIntakeRecord` is enriched with optional `callback_time`, `customer_type`, `transcript`, `ai_summary`, `notify_owner`, and `sms_sent` fields for finalized-call integrations.
- D028: `normalize_phone()` returns normalized E.164 output for supported North American inputs and `None` for unusable values; provider layers convert invalid-required inputs into typed CRM/SMS failures.
- D029: `GoHighLevelService` treats search results as candidates only and chooses create vs update solely by exact shared-phone normalization equality.
- D030: `TwilioSmsService` normalizes owner/sender numbers, skips disabled or already-sent alerts before any request, and uses a concise summary-first owner message with a fallback derived from issue/danger context.

## Blockers

- None. The full S04 verification gate is green.

## Next Action

Start S05 by wiring the call lifecycle: after-hours gate, transcript/summary finalization, CRM write, SMS send, and partial-call handling using the completed CRM and alert protocol boundaries.
