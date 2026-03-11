# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| D001 | M001 | arch | Language | Python | Scaffold is Python; LiveKit Agents SDK is Python-first; spec TS type notation is translated to Python dataclasses | No |
| D002 | M001 | arch | Module layout | Flat modules under `src/` (no subdirectory packages in initial approach) with explicit imports | Simpler than nested packages for a single-milestone build; agent.py entrypoint requirement means src/ is already on path | Yes — if codebase grows large |
| D003 | M001 | arch | Slot-filling mechanism | `AgentTask` subclass with `@function_tool` decorators for slot recording; one tool per slot or grouped by intent | LiveKit AgentTask is the idiomatic pattern for discrete collection tasks; function tools give LLM clear structured extraction targets | Yes — revisit if tool-call reliability is poor |
| D004 | M001 | arch | Safety branch | `session.update_agent(SafetyAgent())` via function tool trigger when LiveClassifier detects danger | Idiomatic LiveKit handoff; keeps safety logic in a separate minimal agent with no intake tools | No |
| D005 | M001 | arch | Timezone handling | Python stdlib `zoneinfo` (Python 3.10+) | Project requires Python >=3.10; zoneinfo is stdlib, no extra dep needed | Yes — if pytz compatibility needed |
| D006 | M001 | arch | HTTP client for integrations | `httpx` with async client | Async-first; fits LiveKit's async event loop; cleaner than aiohttp for REST | Yes — if aiohttp already in deps |
| D007 | M001 | arch | SMS provider | Twilio as default; abstracted behind AlertService protocol | Most common; good Python client; spec does not mandate a provider; protocol abstraction allows swap | Yes — if provider preference changes |
| D008 | M001 | convention | Config types | Python dataclasses (not Pydantic) for `BusinessConfig` and `CallIntakeRecord` | Keeps deps minimal; Pydantic not in current pyproject.toml; dataclasses sufficient for this scale | Yes — if validation complexity grows |
| D009 | M001 | arch | Background classification timing | Live classifier runs synchronously in conversation_item_added event handler (lightweight keyword check); final classifier runs as background asyncio task post-call using LLM | Live check must be <10ms to not block; LLM-based final classification can be async post-call | No |
| D010 | M001 | convention | CRM write timing | Async post-call, in a background task fired from call lifecycle finalize(); does not block session teardown | CRM latency must not affect voice session quality | No |
| D011 | M001 | convention | Duplicate alert prevention | Track `sms_sent` boolean on `CallIntakeRecord` / lifecycle state; check before send | Simple, sufficient for V1 single-call scope | Yes — if multi-worker deployment needs distributed lock |
| D012 | M001 | scope | GoHighLevel API version | v2 API (`https://services.leadconnectorhq.com`) with Authorization: Bearer token | GHL v1 is deprecated; v2 is current; Bearer token auth is standard | No |
| D013 | M001 | convention | Type module names | `src/hvac_types/` and `src/config/` as subdirectories | Subdirectories map better to the spec boundaries; naming `hvac_types` instead of `types` avoids shadowing the Python stdlib `types` module. | No |
| D014 | S01/T01 | convention | str Enum __str__ | All `str, Enum` subclasses override `__str__` to `return self.value` | Python 3.11+ changed `str(StrEnum.MEMBER)` from returning the value to `'ClassName.MEMBER'`; project runs 3.13.2; override restores expected behaviour across all versions and ensures enum values match LLM output tokens directly | No |
| D015 | S01/T03 | convention | Config boot validation | `load_config()` performs eager required-field validation (`business_name`, `timezone`, `owner_phone`) with whitespace-aware non-empty string checks before runtime use | Fails fast on misconfiguration during initialization so downstream call/dispatch flows never start with invalid core business identity/contact context | Yes — revisit if config schema migrates to a dedicated validation library |
