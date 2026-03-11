# S01: Core Types, Config, and Data Model — Research

**Date:** 2026-03-11
**Slice:** S01 — Core Types, Config, and Data Model
**Risk:** low
**Dependencies:** none

---

## Summary

S01 is a pure data-layer slice: no LiveKit SDK calls, no async code, no external APIs. Its job is to define all the typed structures that every downstream slice imports — `CallIntakeRecord`, `BusinessConfig`, slot types, classification enums, and the HVAC demo config singleton. Because this slice has no behavioural logic, it is fast to write and can be exhaustively unit-tested without any LiveKit context.

The key design choice locked in via D008 (Python dataclasses, not Pydantic) keeps the dependency graph clean. All types in this slice must be importable from `src/` by downstream slices without triggering any LiveKit, httpx, or third-party imports, since `src/agent.py` serves as the module root and downstream slices import types directly.

D002 (flat modules under `src/`) means each module is a plain `.py` file — no `__init__.py` package structure needed for this slice. The existing `src/agent.py` is already on the Python path through `pyproject.toml`'s `setuptools.package-dir` configuration, so all new files under `src/` are immediately importable without further setup.

The `load_config()` validator must raise `ValueError` with a descriptive message for any missing required field (owner phone, business name, business timezone). This is the only execution-time entry point in S01 and must fail fast so downstream slices don't receive a half-configured `BusinessConfig`.

---

## Recommendation

Use `@dataclass` with `field(default_factory=...)` for mutable defaults (lists) and plain `= None` for optional scalar fields. Use `Enum` from stdlib for `SlotStatus`, `IssueCategory`, `UrgencyLevel`, and `DangerType`. Write `hvac_demo_config.py` as a module-level constant (`HVAC_DEMO_CONFIG: BusinessConfig = BusinessConfig(...)`) — do not wrap it in a factory function; it is a pure config value with no side effects.

`load_config()` in `load_config.py` should accept an optional `BusinessConfig` parameter and validate it; if none is supplied it falls back to `HVAC_DEMO_CONFIG`. This makes the function testable without filesystem mocking.

Write unit tests covering: all enum values are importable, required-field validation raises on empty strings and `None`, `CallIntakeRecord` starts with all slots `MISSING`, `SlotState` transitions are representable, and `HVAC_DEMO_CONFIG` passes its own validator.

---

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Optional typed fields on a dataclass | `from dataclasses import dataclass, field` + `X \| None = None` (Python 3.10+) | Native stdlib; no third-party import; consistent with LiveKit SDK's own session-state dataclasses |
| Enum with string values | `from enum import Enum` + `class MyEnum(str, Enum)` | `str` mixin lets enum values serialize directly to JSON strings without extra serialization step — useful for CRM payloads |
| Mutable default lists on dataclass | `field(default_factory=list)` | Avoids the classic shared-mutable-default bug that plagues plain `= []` on dataclasses |

---

## Existing Code and Patterns

- `src/agent.py` — Contains the `Assistant(Agent)` class and `AgentServer` wiring. Must not be touched in S01. Its import structure (`from livekit.agents import ...`) shows that `src/` is the module root; new modules at `src/types_foo.py` are imported as `from types_foo import ...` in tests. Note: the existing test at `tests/test_agent.py` imports `from agent import Assistant` (not `from src.agent`), confirming `src/` is the Python path root.
- `tests/test_agent.py` — Uses `AgentSession` + `inference.LLM` pattern for eval tests. S01 unit tests do NOT need `AgentSession` — they are plain pytest with no async; dataclass field assertions are synchronous.
- `pyproject.toml` — `requires-python = ">=3.10, <3.15"` confirms `zoneinfo` is available (Python 3.9+ stdlib). No `httpx`, no `pydantic`, no `twilio` yet — S01 must add nothing to `[dependencies]`. `asyncio_mode = "auto"` in pytest config means sync tests work fine without extra markers.

---

## Constraints

- **No new dependencies in `[dependencies]`** — S01 is pure stdlib. `dataclasses`, `enum`, `datetime`, `zoneinfo`, `typing` are all in scope. `httpx` and `twilio` come in S04.
- **`src/` is the package root** — all modules at `src/types_*.py`, `src/config/*.py` etc. must be importable as `from types_foo import ...` from tests. Because `pyproject.toml` sets `package-dir = {"" = "src"}`, setuptools will find packages inside `src/`. But since D002 specifies flat modules (no subdirectory packages), files like `src/config/load_config.py` require `src/config/__init__.py` to be importable as `from config.load_config import load_config`. If subdirectories are used, `__init__.py` files must be added.
- **D002 ambiguity — flat vs subdirectory** — The roadmap boundary map specifies paths like `src/config/hvac_demo_config.py` and `src/types/call_intake_record.py`, implying subdirectories. But D002 says "flat modules under `src/`". Resolution: use subdirectories as specified in the boundary map (they are cleaner at this scale), but add `__init__.py` to each subdirectory. The D002 rationale ("simpler than nested packages") remains valid for the overall project; S01's subdirectories are shallow and unambiguous. Document this as a clarification in DECISIONS.md.
- **`ruff target-version = "py39"`** — The ruff config sets `py39` but `requires-python = ">=3.10"`. This means `X | Y` union type syntax (PEP 604, Python 3.10+) will be flagged by ruff if used in annotations directly. Use `Optional[X]` from `typing` or `from __future__ import annotations` at the top of each file to keep ruff happy while using the cleaner syntax in docstrings.
- **`str` enum mixin** — All classification enums should use `class Foo(str, Enum)` so that values serialize to their string representation for JSON/CRM payloads without needing `.value` access.

---

## File Map (what to produce)

```
src/
  types/
    __init__.py
    call_intake_record.py   — CallIntakeRecord dataclass
    business_config.py      — BusinessConfig dataclass
    slot_state.py           — SlotStatus(str, Enum), SlotState dataclass
    classification.py       — IssueCategory, UrgencyLevel, DangerType enums
  config/
    __init__.py
    hvac_demo_config.py     — HVAC_DEMO_CONFIG: BusinessConfig
    load_config.py          — load_config(config=None) -> BusinessConfig
tests/
  test_types.py             — unit tests for all types and config validation
```

---

## Type Design Notes

### `SlotStatus`

```python
class SlotStatus(str, Enum):
    MISSING = "missing"
    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"
```

Transitions are one-way: MISSING → TENTATIVE → CONFIRMED. Downgrade is not needed for V1 (D003).

### `SlotState`

```python
@dataclass
class SlotState:
    status: SlotStatus = SlotStatus.MISSING
    value: str | None = None   # raw captured value
    confidence: float = 0.0    # 0.0–1.0; < threshold → TENTATIVE
```

Threshold for TENTATIVE vs CONFIRMED lives in `IntakePolicy` (S02), not in this type.

### `CallIntakeRecord`

Required fields for CRM (all eventually filled): `call_id`, `caller_phone`, `caller_name`, `callback_number`, `issue_summary`, `callback_time`.

Optional: `service_address` (only collected when `address_relevant=True` per classifier), `customer_type`, `issue_category`, `urgency_level`, `urgency_reason`, `ai_summary`, `transcript`, `danger_detected`, `notify_owner`, `call_status`, `sms_sent`, `started_at`, `ended_at`.

`call_status` should be a `str` enum: `"partial"` | `"complete"`. Use a simple `CallStatus(str, Enum)` in `call_intake_record.py`.

All slot-level state (`caller_name_slot`, `callback_number_slot`, etc.) is managed by `SlotTracker` in S02, not stored on `CallIntakeRecord`. `CallIntakeRecord` holds finalized values only.

### `BusinessConfig`

Fields from spec: `business_name`, `timezone` (str, e.g. `"America/Toronto"`), `after_hours_start` (int hour, e.g. 17), `after_hours_end` (int hour, e.g. 9), `owner_phone`, `owner_sms_enabled` (bool), `safety_keywords` (list[str]), `urgent_keywords` (list[str]), `safety_message` (str), `business_greeting` (str).

All keyword lists use `field(default_factory=list)`.

### `IssueCategory` / `UrgencyLevel` / `DangerType`

```python
class IssueCategory(str, Enum):
    NO_HEAT = "no_heat"
    NO_COOL = "no_cool"
    STRANGE_NOISE = "strange_noise"
    WATER_LEAK = "water_leak"
    ELECTRICAL = "electrical"
    GAS_SMELL = "gas_smell"
    OTHER = "other"

class UrgencyLevel(str, Enum):
    STANDARD = "standard"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class DangerType(str, Enum):
    GAS = "gas"
    CO = "co"
    FIRE = "fire"
    ELECTRICAL = "electrical"
    FLOODING = "flooding"
    NONE = "none"
```

---

## Common Pitfalls

- **`ruff` `py39` target with `X | Y` syntax** — `X | Y` union annotations require Python 3.10+ at runtime but ruff's `py39` target will flag them as `UP007`. Mitigation: add `from __future__ import annotations` to every file that uses `X | Y` syntax, or use `Optional[X]` from typing. The `from __future__` approach is cleaner since `pyproject.toml`'s `requires-python` already guarantees 3.10.
- **Mutable defaults on dataclasses** — `safety_keywords: list[str] = []` is a runtime error. Always use `field(default_factory=list)`.
- **`__init__.py` missing from subdirectories** — Without `__init__.py`, `from types.call_intake_record import CallIntakeRecord` fails. Every subdirectory used as a package needs an empty `__init__.py`. Note that `types` conflicts with the stdlib `types` module — name the import path `src.types` or, better, name the subdirectory `hvac_types` or use `from types.call_intake_record` only after confirming the import resolution order. **Risk: naming a subdirectory `types` shadows the stdlib `types` module.** Safest approach: name the directory `hvac_types` or just use the roadmap's flat naming with file prefixes.
- **`datetime.datetime` without timezone for `started_at`/`ended_at`** — Always store as UTC-aware datetimes (`datetime.now(timezone.utc)`), not naive datetimes. Otherwise timezone arithmetic in the after-hours gate (S05) becomes fragile.
- **`load_config()` mutating the HVAC_DEMO_CONFIG singleton** — Validator must not modify the passed-in config. It should raise on invalid, return unchanged config on valid.

---

## Open Risks

- **`types` subdirectory name collision** — Python stdlib has a `types` module. Naming the subdirectory `src/types/` and then doing `from types.call_intake_record import ...` may shadow stdlib `types`. Needs a quick import verification test. Mitigation: if there's a conflict, rename to `src/models/` or just prefix files flat in `src/` (e.g. `src/call_intake_record.py`). The roadmap uses `src/types/` — a decision here should go to DECISIONS.md.
- **`from __future__ import annotations` interaction with runtime type introspection** — If any code later uses `dataclasses.fields()` and inspects `field.type` at runtime (e.g. for serialization), `from __future__ import annotations` makes all annotations strings, not live types. This could break serialization code in S04. Mitigation: use `typing.get_type_hints()` instead of `field.type` for any runtime introspection. Document this in S04's research.
- **ruff `target-version = "py39"` inconsistency** — The project requires Python 3.10 but ruff targets 3.9. This is a pre-existing inconsistency. For S01, work around it with `from __future__ import annotations`. In S06, update ruff config to `target-version = "py310"` as part of the polish pass.

---

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LiveKit Agents | `livekit-agents` (project-local) | Installed — `.agents/skills/livekit-agents/SKILL.md` |

No additional skills needed for S01 — this is pure Python stdlib work.

---

## Sources

- `AgentTask` uses `@dataclass` result types natively; pattern confirmed in SDK docs (source: [LiveKit Agents — Tasks](https://docs.livekit.io/agents/build/tasks))
- `userdata` on `AgentSession` uses dataclass with optional typed fields as idiomatic pattern (source: [LiveKit Agents — Handoffs](https://docs.livekit.io/agents/logic/agents-handoffs))
- `BehavioralResults` dataclass in unordered collection example shows exactly the `CallIntakeRecord`-shaped pattern we need (source: [LiveKit Agents — Tasks](https://docs.livekit.io/agents/build/tasks))
- `pyproject.toml` `requires-python = ">=3.10"` confirms `zoneinfo` stdlib availability; existing `src/agent.py` import pattern confirms `src/` is the module root
- Existing `tests/test_agent.py` `from agent import Assistant` confirms flat import from `src/`
