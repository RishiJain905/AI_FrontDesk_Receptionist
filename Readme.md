# 🏢 AI Front Desk Receptionist — HVAC After-Hours Voice Agent

An intelligent, voice-powered AI receptionist that handles after-hours HVAC service calls. Built on [LiveKit Agents](https://docs.livekit.io/agents/), the system autonomously conducts intake conversations, classifies caller urgency, and routes outcomes to a CRM and SMS alerting pipeline — no human intervention required.

---

## ✨ Features

- **Voice-First AI Pipeline** — Real-time speech-to-text (Deepgram Nova 3), LLM reasoning (OpenAI GPT-4.1 Mini), and text-to-speech (Cartesia Sonic 3) for natural, human-like conversations.
- **After-Hours Gate** — Automatically determines whether the call falls within configured after-hours windows before engaging the intake flow.
- **Structured Intake & Slot Filling** — Guided conversation to collect caller name, callback number, issue summary, and preferred callback time.
- **Safety Escalation Detection** — Real-time and final classification of danger keywords (gas leak, CO alarm, sparks, etc.) triggers immediate safety-first handoff behavior and owner SMS alerts.
- **CRM Integration (GoHighLevel)** — Upserts contacts and attaches call notes to GoHighLevel automatically after every call.
- **SMS Owner Alerts (Twilio)** — Sends owner notifications via Twilio when safety escalation is detected (`notify_owner=true`).
- **Graceful Degradation** — If CRM or SMS credentials are missing, the agent falls back to no-op provider stubs so development/testing can continue uninterrupted. Provider failures are isolated — one integration failure never blocks the other.
- **Full Call Lifecycle Management** — Structured lifecycle logging (`finalize_started` → `crm_result` → `sms_result` → `finalize_completed`) with inspectable state snapshots for debugging.
- **Noise Cancellation** — LiveKit BVC telephony-grade noise cancellation for crystal-clear voice input.
- **Comprehensive Test Suite** — 13 test modules covering agent behavior, call lifecycle, slot filling, conversation control, CRM/SMS services, safety classification, and S06 milestone readiness.

---

## 🏗️ Architecture

```
src/
├── agent.py                    # LiveKit agent entry point & session wiring
├── classification/             # Safety & urgency classifiers (live + final)
│   ├── final_classifier.py     # Post-call classification
│   ├── live_classifier.py      # Real-time in-call classification
│   └── rules.py                # Keyword & pattern matching rules
├── config/                     # Business configuration & loading
│   ├── hvac_demo_config.py     # Demo/default HVAC business config
│   └── load_config.py          # Environment-driven config loader
├── conversation/               # Conversation management
│   ├── conversation_controller.py  # Main HVAC conversation controller
│   ├── intake_policy.py        # Intake flow policy & logic
│   ├── intake_task.py          # Slot-filling intake task
│   ├── prompts.py              # System & greeting prompts
│   └── slot_tracker.py         # Tracks required intake slots
├── hvac_types/                 # Domain types & data models
│   ├── business_config.py      # Business configuration schema
│   ├── call_intake_record.py   # Call intake record structure
│   ├── classification.py       # Classification result types
│   └── slot_state.py           # Slot state definitions
├── orchestration/              # Call flow orchestration
│   ├── after_hours_gate.py     # After-hours time window check
│   ├── call_lifecycle.py       # End-to-end call lifecycle management
│   ├── summary_builder.py      # Post-call summary generation
│   └── transcript_assembler.py # Transcript assembly utilities
├── services/                   # External service integrations
│   ├── alerts/                 # SMS alerting (Twilio)
│   └── crm/                    # CRM integration (GoHighLevel)
└── utils/                      # Shared utilities
    ├── errors.py               # Error handling & typed exceptions
    ├── logging.py              # Structured lifecycle logging
    ├── phone.py                # Phone number normalization
    └── time.py                 # Time/timezone utilities
```

---

## 🔧 Tech Stack

| Layer             | Technology                              |
| ----------------- | --------------------------------------- |
| **Runtime**       | Python 3.12+                            |
| **Voice Platform**| LiveKit Agents SDK                      |
| **STT**           | Deepgram Nova 3 (multilingual)          |
| **LLM**           | OpenAI GPT-4.1 Mini                     |
| **TTS**           | Cartesia Sonic 3                        |
| **VAD**           | Silero VAD                              |
| **Turn Detection**| LiveKit Multilingual Turn Detector      |
| **Noise Cancel**  | LiveKit BVC Telephony                   |
| **CRM**           | GoHighLevel API                         |
| **SMS**           | Twilio                                  |
| **HTTP Client**   | HTTPX (async)                           |
| **Package Mgmt**  | uv                                      |
| **Linting**       | Ruff                                    |
| **Testing**       | pytest + pytest-asyncio                 |

---

## ⚡ Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
cd my-agent
uv sync --dev
```

### Environment Setup

Copy the template and fill in your credentials:

```bash
cp .env.example .env.local
```

> ⚠️ Keep secrets out of git. `.env.local` and `.env` are gitignored.

#### Required Environment Variables

| Variable               | Service       | Description                    |
| ---------------------- | ------------- | ------------------------------ |
| `LIVEKIT_URL`          | LiveKit       | Your LiveKit server URL        |
| `LIVEKIT_API_KEY`      | LiveKit       | API key for LiveKit            |
| `LIVEKIT_API_SECRET`   | LiveKit       | API secret for LiveKit         |
| `GHL_API_TOKEN`        | GoHighLevel   | API token for CRM integration  |
| `GHL_LOCATION_ID`      | GoHighLevel   | Location ID for CRM records    |
| `TWILIO_ACCOUNT_SID`   | Twilio        | Account SID for SMS            |
| `TWILIO_AUTH_TOKEN`    | Twilio        | Auth token for SMS             |
| `TWILIO_FROM_NUMBER`   | Twilio        | Outbound SMS phone number      |

> If GoHighLevel or Twilio keys are missing, the agent falls back to no-op stubs so local runs still complete.

---

## 🚀 Running the Agent

### Console Mode (terminal-driven testing)

```bash
uv run python src/agent.py console
```

### Dev Mode (LiveKit dev loop)

```bash
uv run python src/agent.py dev
```

---

## 🧪 Testing

Run the full test suite:

```bash
uv run pytest
```

Run linting and formatting checks:

```bash
uv run ruff check src/
uv run ruff format --check src/
```

Milestone readiness checks:

```bash
uv run pytest tests/test_s06_readiness.py -q
```

---

## 📞 Demo Scenarios

### 1. Normal Intake Path
- Start in `console` mode
- Simulate a typical after-hours HVAC issue (no safety terms)
- Provide name, callback number, issue summary, and callback time
- **Expected:** Call closes cleanly, CRM persistence is attempted, no owner SMS sent

### 2. Safety Escalation Path
- Start a new call and include danger language (e.g., *"gas smell"*, *"CO alarm"*, *"sparks"*)
- **Expected:** Immediate safety-first handoff, CRM persistence still attempted, owner SMS sent

### 3. Partial Hang-Up Path
- Start intake and terminate early before all slots are confirmed
- **Expected:** Finalization still runs, call status is partial, CRM persistence still attempted

### Post-Call Guarantees
- ✅ CRM record is **always** attempted on finalized calls (complete or partial)
- ✅ SMS is **conditional** — sent only when `notify_owner=true`
- ✅ Provider failures are **isolated** — one failure never blocks the other

---

## 📄 License

This project is licensed under a **proprietary, all-rights-reserved license**. See [LICENSE](./LICENSE) for details.

**You may NOT copy, modify, distribute, sublicense, or use this software** in any form without explicit written permission from the author.
