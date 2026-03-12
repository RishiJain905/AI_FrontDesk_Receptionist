"""LiveKit intake task for tool-driven HVAC slot filling.

This task wraps the deterministic S02 slot tracker, policy, and classifier core in a
real LiveKit ``AgentTask``. The LLM is responsible for conversational phrasing, while
structured slot mutations happen only through explicit function tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from livekit.agents import AgentTask, function_tool, llm

from classification.live_classifier import LiveClassification, LiveClassifier
from conversation.intake_policy import IntakeMode, get_required_slots
from conversation.slot_tracker import SlotTracker
from hvac_types.classification import DangerType, IssueCategory
from hvac_types.slot_state import SlotState, SlotStatus

_DEFAULT_REQUIRED_SLOTS = get_required_slots(
    mode=IntakeMode.NORMAL,
    address_relevant=True,
)

_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})\b")
_NAME_RE = re.compile(
    r"\b(?:this is|my name is)\s+(?P<tentative>maybe\s+)?(?P<name>[A-Za-z][A-Za-z' -]{0,40}?)(?=,|\.| and\b|$)",
    flags=re.IGNORECASE,
)
_ADDRESS_RE = re.compile(
    r"\b(?P<prefix>i think the address is|the address is|address is)\s+(?P<address>.+?)(?=\.|$)",
    flags=re.IGNORECASE,
)
_CONFIRMATION_RE = re.compile(
    r"\b(?:yes|correct|that'?s right|confirmed)\b", flags=re.IGNORECASE
)


class ProposedActionType(str, Enum):
    """Deterministic tool action recommendations for the current turn."""

    RECORD = "record"
    CONFIRM = "confirm"


@dataclass(frozen=True)
class ProposedAction:
    """Structured recommendation injected into the task instructions."""

    action_type: ProposedActionType
    slot_name: str
    value: str
    confidence: float | None = None
    confirmed: bool = False
    reason: str = ""


@dataclass(frozen=True)
class IntakeTaskResult:
    """Inspectable task result emitted when intake safely completes."""

    slots: dict[str, SlotState]
    required_slots: tuple[str, ...]
    missing_required_slots: tuple[str, ...]
    tentative_slots: tuple[str, ...]
    classification: LiveClassification


class IntakeTask(AgentTask[IntakeTaskResult]):
    """Collect HVAC intake slots with explicit tools and safe completion guards."""

    def __init__(
        self,
        *,
        tracker: SlotTracker | None = None,
        classifier: LiveClassifier | None = None,
        mode: IntakeMode = IntakeMode.NORMAL,
        chat_ctx: llm.ChatContext | None = None,
    ) -> None:
        self._classifier = classifier or LiveClassifier()
        self._mode = mode
        self._tracker = tracker or SlotTracker(required_slots=_DEFAULT_REQUIRED_SLOTS)
        self._cumulative_transcript = ""
        self._latest_user_turn = ""
        self._classification = self._classifier.classify("")
        self._completion_requested = False
        super().__init__(instructions=self._build_instructions(), chat_ctx=chat_ctx)

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ) -> None:
        transcript = (new_message.text_content or "").strip()
        self._latest_user_turn = transcript
        self._cumulative_transcript = " ".join(
            part for part in [self._cumulative_transcript, transcript] if part
        )
        if self._cumulative_transcript:
            self._classification = self._classifier.classify(
                self._cumulative_transcript
            )

        proposed_actions = self._propose_actions(transcript)
        await self.update_instructions(
            self._build_instructions(
                latest_user_turn=transcript,
                proposed_actions=proposed_actions,
            )
        )
        turn_ctx.add_message(
            role="assistant",
            content=(
                "Structured intake controller note for the model only. Follow the task "
                f"instructions exactly. Current blocking state: {self._guard_summary()}."
            ),
        )

    @function_tool()
    async def record_slot_candidate(
        self,
        slot_name: str,
        value: str,
        confidence: float = 1.0,
        confirmed: bool = False,
    ) -> str:
        """Record a slot value extracted from the caller's latest turn.

        Use this tool whenever the caller directly provides a slot value that should be stored in
        structured state. Set ``confirmed=true`` only when the caller stated the value clearly and
        confidently in the current turn. Set ``confirmed=false`` when the wording is uncertain,
        approximate, or needs explicit caller confirmation before intake can complete. Do not use
        this tool to confirm a previously tentative slot when the purpose of the turn is an
        explicit yes/no confirmation; use ``confirm_slot`` for that case instead.

        Args:
            slot_name: Canonical slot name such as customer_name, phone_number, service_address, or issue_category.
            value: Exact normalized slot value to store.
            confidence: Extraction confidence from 0.0 to 1.0; use a low value for tentative guesses.
            confirmed: Whether this turn should promote the stored value directly to confirmed state.
        """

        normalized_value = self._coerce_slot_value(slot_name, value)
        current = self._tracker.snapshot().get(slot_name)
        if (
            current
            and current.status == SlotStatus.CONFIRMED
            and current.value == normalized_value
        ):
            return self._guard_summary(prefix=f"{slot_name} already confirmed")

        current = self._tracker.snapshot().get(slot_name)
        should_promote_to_confirmed = confirmed
        if slot_name == "issue_category":
            should_promote_to_confirmed = True
        elif (
            current is not None
            and current.status == SlotStatus.FILLED
            and self._has_confirmation_cue(self._latest_user_turn)
            and slot_name in {"customer_name", "service_address"}
        ):
            should_promote_to_confirmed = True

        if should_promote_to_confirmed:
            self._tracker.confirm(slot_name, normalized_value)
        else:
            bounded_confidence = max(0.0, min(confidence, 1.0))
            self._tracker.record_candidate(
                slot_name,
                normalized_value,
                confidence=bounded_confidence,
            )

        return self._guard_summary(prefix=f"recorded {slot_name}")

    @function_tool()
    async def confirm_slot(self, slot_name: str, value: str | None = None) -> str:
        """Confirm a previously tentative slot after the caller explicitly validates it.

        Use this only when the caller clearly confirms an already-recorded tentative value or
        corrects it with a definitive replacement. Do not use this for brand-new information that
        has not been stored yet; use ``record_slot_candidate`` first for new data.

        Args:
            slot_name: Canonical slot name whose value is being confirmed.
            value: Optional corrected replacement value. Omit when confirming the existing candidate as-is.
        """

        normalized_value = (
            None if value is None else self._coerce_slot_value(slot_name, value)
        )
        self._tracker.confirm(slot_name, normalized_value)
        return self._guard_summary(prefix=f"confirmed {slot_name}")

    @function_tool(name="clear_slot")
    async def clear_slot(self, slot_name: str) -> str:
        """Clear a slot when the caller rejects or retracts the current value.

        Use this when the caller says a stored value is wrong, uncertain, or should be removed so
        the agent can re-ask for it. Do not use this when the caller is simply confirming a value.

        Args:
            slot_name: Canonical slot name to reset back to missing.
        """

        self._tracker.reject(slot_name)
        return self._guard_summary(prefix=f"cleared {slot_name}")

    @function_tool()
    async def complete_intake(self) -> str:
        """Finish the intake task once every currently required slot is confirmed.

        Use this exactly once, and only after the policy-required slots are confirmed in structured
        state. If any required slot is still missing or tentative, this tool must not complete the
        task and will return the blocking state instead.
        """

        if self._completion_requested or self.done():
            return self._guard_summary(prefix="intake already completed")

        if not self._all_required_confirmed():
            return self._guard_summary(prefix="completion blocked")

        self._completion_requested = True
        self.complete(self._build_result())
        return self._guard_summary(prefix="intake completed")

    def _build_instructions(
        self,
        *,
        latest_user_turn: str | None = None,
        proposed_actions: list[ProposedAction] | None = None,
    ) -> str:
        required_slots = self._current_required_slots()
        missing_slots = self._missing_required_slots()
        tentative_slots = self._tentative_required_slots()
        slot_snapshot = self._format_snapshot(self._tracker.snapshot())
        action_lines = self._format_proposed_actions(proposed_actions or [])
        response_requirements = self._build_response_requirements(
            proposed_actions or []
        )
        latest_turn_block = latest_user_turn or "<none>"

        return f"""
You are the after-hours HVAC intake task for North Star HVAC.

Your job is to keep structured slot state synchronized through function tools and then speak to the
caller naturally. Never rely on prose alone to remember intake data.

Rules you must follow on every turn:
1. Treat the deterministic controller recommendations below as the default plan for this turn.
   When recommendations are present, execute those tool calls in the listed order and keep the
   listed arguments unless the user's words plainly contradict them.
2. Before any assistant message, use function tools to record or confirm every reliable slot value
   present in the caller's latest turn.
3. Use record_slot_candidate for newly provided information.
4. Set record_slot_candidate.confirmed=true when the caller stated the value clearly and directly.
5. Set record_slot_candidate.confirmed=false only when the wording is tentative, such as maybe,
   I think, approximately, or otherwise uncertain.
6. Use confirm_slot only when the caller explicitly confirms a slot that was already tentative
   BEFORE this user turn. Never use confirm_slot for a brand-new value first mentioned in the same
   turn, and never promote a tentative value to confirmed unless the caller clearly validates it.
7. Do not ask the caller to confirm an issue category when the controller marks it confirmed.
8. Never call complete_intake until every CURRENTLY REQUIRED slot is confirmed.
9. If completion is possible after your tool calls, call complete_intake immediately before your
   assistant message.
10. If completion is not possible, do NOT say intake is complete. Ask only for the still-missing
   required slots or explicit confirmation of tentative required slots. Ask for every missing
   required slot in the same reply.
11. Your assistant reply MUST explicitly acknowledge every structured detail captured from this
   turn before asking for anything else. Do not omit the callback number or reported issue when
   they were captured this turn.
12. Do not re-ask already confirmed slots.
13. Be concise and phone-call friendly.

Current classification:
- danger_type: {self._classification.danger_type}
- urgency_level: {self._classification.urgency_level}
- issue_category: {self._classification.issue_category}
- address_relevant: {self._classification.address_relevant}
- matched_keywords: {", ".join(self._classification.matched_keywords) or "<none>"}

Current required slots: {", ".join(required_slots) or "<none>"}
Missing required slots: {", ".join(missing_slots) or "<none>"}
Tentative required slots needing confirmation: {", ".join(tentative_slots) or "<none>"}
Current slot snapshot: {slot_snapshot}
Latest user turn: {latest_turn_block}

Deterministic controller recommendations for this turn:
{action_lines}

Required content for your next assistant message after tool calls:
{response_requirements}
""".strip()

    def _propose_actions(self, transcript: str) -> list[ProposedAction]:
        if not transcript:
            return []

        actions: list[ProposedAction] = []
        snapshot = self._tracker.snapshot()

        name_candidate = self._extract_name(transcript)
        if name_candidate is not None:
            current_name = snapshot.get("customer_name")
            is_confirming_existing = (
                current_name is not None
                and current_name.status == SlotStatus.FILLED
                and self._has_confirmation_cue(transcript)
                and not name_candidate[1]
            )
            if is_confirming_existing:
                actions.append(
                    ProposedAction(
                        action_type=ProposedActionType.CONFIRM,
                        slot_name="customer_name",
                        value=name_candidate[0],
                        reason="Caller explicitly confirmed the previously tentative name.",
                    )
                )
            else:
                actions.append(
                    ProposedAction(
                        action_type=ProposedActionType.RECORD,
                        slot_name="customer_name",
                        value=name_candidate[0],
                        confidence=0.55 if name_candidate[1] else 0.98,
                        confirmed=not name_candidate[1],
                        reason=(
                            "Name wording is tentative and needs confirmation."
                            if name_candidate[1]
                            else "Caller stated their name directly."
                        ),
                    )
                )

        phone_number = self._extract_phone_number(transcript)
        if phone_number is not None:
            actions.append(
                ProposedAction(
                    action_type=ProposedActionType.RECORD,
                    slot_name="phone_number",
                    value=phone_number,
                    confidence=0.99,
                    confirmed=True,
                    reason="Caller directly stated a callback number.",
                )
            )

        address_candidate = self._extract_address(transcript)
        if address_candidate is not None:
            current_address = snapshot.get("service_address")
            is_confirming_existing = (
                current_address is not None
                and current_address.status == SlotStatus.FILLED
                and self._has_confirmation_cue(transcript)
                and not address_candidate[1]
            )
            if is_confirming_existing:
                actions.append(
                    ProposedAction(
                        action_type=ProposedActionType.CONFIRM,
                        slot_name="service_address",
                        value=address_candidate[0],
                        reason="Caller explicitly confirmed the previously tentative address.",
                    )
                )
            else:
                actions.append(
                    ProposedAction(
                        action_type=ProposedActionType.RECORD,
                        slot_name="service_address",
                        value=address_candidate[0],
                        confidence=0.55 if address_candidate[1] else 0.97,
                        confirmed=not address_candidate[1],
                        reason=(
                            "Address wording is tentative and needs confirmation."
                            if address_candidate[1]
                            else "Caller stated the service address clearly."
                        ),
                    )
                )

        current_issue = snapshot.get("issue_category")
        turn_classification = self._classifier.classify(transcript)
        if (
            turn_classification.danger_type == DangerType.NONE
            and turn_classification.issue_category != IssueCategory.OTHER
            and turn_classification.matched_keywords
            and not (
                current_issue
                and current_issue.status == SlotStatus.CONFIRMED
                and current_issue.value == turn_classification.issue_category
            )
        ):
            actions.append(
                ProposedAction(
                    action_type=ProposedActionType.RECORD,
                    slot_name="issue_category",
                    value=str(turn_classification.issue_category),
                    confidence=0.95,
                    confirmed=True,
                    reason="Deterministic classifier found a supported HVAC issue category.",
                )
            )

        return actions

    def _current_required_slots(self) -> list[str]:
        issue_category = self._slot_issue_category()
        mode = (
            IntakeMode.DANGER_MINIMUM
            if self._classification.danger_type != DangerType.NONE
            else self._mode
        )
        address_relevant = self._classification.address_relevant
        if issue_category is not None:
            address_relevant = None

        return get_required_slots(
            mode=mode,
            address_relevant=address_relevant,
            danger_type=self._classification.danger_type,
            issue_category=issue_category,
        )

    def _slot_issue_category(self) -> IssueCategory | None:
        slot = self._tracker.snapshot().get("issue_category")
        if slot is None or slot.value is None:
            if self._classification.issue_category == IssueCategory.OTHER:
                return None
            return self._classification.issue_category
        if isinstance(slot.value, IssueCategory):
            return slot.value
        return self._parse_issue_category(str(slot.value))

    def _missing_required_slots(self) -> list[str]:
        snapshot = self._tracker.snapshot()
        return [
            slot_name
            for slot_name in self._current_required_slots()
            if snapshot.get(slot_name, SlotState()).status == SlotStatus.EMPTY
        ]

    def _tentative_required_slots(self) -> list[str]:
        snapshot = self._tracker.snapshot()
        return [
            slot_name
            for slot_name in self._current_required_slots()
            if snapshot.get(slot_name, SlotState()).status == SlotStatus.FILLED
        ]

    def _all_required_confirmed(self) -> bool:
        snapshot = self._tracker.snapshot()
        required_slots = self._current_required_slots()
        return all(
            snapshot.get(slot_name, SlotState()).status == SlotStatus.CONFIRMED
            for slot_name in required_slots
        )

    def _build_result(self) -> IntakeTaskResult:
        return IntakeTaskResult(
            slots=self._tracker.snapshot(),
            required_slots=tuple(self._current_required_slots()),
            missing_required_slots=tuple(self._missing_required_slots()),
            tentative_slots=tuple(self._tracker.get_tentative_slots()),
            classification=self._classification,
        )

    def _guard_summary(self, *, prefix: str = "state updated") -> str:
        required_slots = self._current_required_slots()
        missing_slots = self._missing_required_slots()
        tentative_slots = self._tentative_required_slots()
        guidance_parts: list[str] = []

        if tentative_slots:
            guidance_parts.append(
                "ask the caller to explicitly confirm "
                + ", ".join(
                    self._slot_prompt_label(slot_name) for slot_name in tentative_slots
                )
            )
        if missing_slots:
            guidance_parts.append(
                "ask for all missing required slots in one reply: "
                + ", ".join(
                    self._slot_prompt_label(slot_name) for slot_name in missing_slots
                )
            )
        issue_slot = self._tracker.snapshot().get("issue_category")
        if issue_slot and issue_slot.status == SlotStatus.CONFIRMED:
            guidance_parts.append(
                "do not ask the caller to confirm the reported issue again"
            )
        if not missing_slots and not tentative_slots and self._completion_requested:
            guidance_parts.append(
                "say the previously tentative details are now confirmed, intake is complete, and summarize the issue succinctly"
            )

        next_reply = (
            "; ".join(guidance_parts) if guidance_parts else "no extra reply guidance"
        )
        return (
            f"{prefix}. required={required_slots}; missing={missing_slots}; "
            f"tentative={tentative_slots}; all_required_confirmed={self._all_required_confirmed()}; "
            f"next_reply={next_reply}"
        )

    def _coerce_slot_value(self, slot_name: str, value: Any) -> Any:
        if slot_name == "issue_category":
            return self._parse_issue_category(str(value))
        if slot_name == "phone_number":
            extracted = self._extract_phone_number(str(value))
            return extracted or str(value).strip()
        return str(value).strip()

    def _parse_issue_category(self, value: str) -> IssueCategory:
        normalized = value.strip().casefold()
        for category in IssueCategory:
            if normalized in {category.value.casefold(), category.name.casefold()}:
                return category

        classified = self._classifier.classify(value).issue_category
        if classified != IssueCategory.OTHER:
            return classified

        simplified = normalized.replace("-", " ").replace("_", " ")
        if "no heat" in simplified or "furnace" in simplified or "heater" in simplified:
            return IssueCategory.NO_HEAT
        if (
            "no cool" in simplified
            or "no cooling" in simplified
            or "cooling" in simplified
            or "air conditioning" in simplified
            or "air conditioner" in simplified
            or "ac" in simplified
        ):
            return IssueCategory.NO_COOL
        if "leak" in simplified or "water" in simplified:
            return IssueCategory.LEAKING_WATER
        if "smell" in simplified or "odor" in simplified:
            return IssueCategory.BAD_SMELL

        msg = f"Unsupported issue_category value: {value}"
        raise ValueError(msg)

    def _format_snapshot(self, snapshot: dict[str, SlotState]) -> str:
        if not snapshot:
            return "<empty>"

        formatted = []
        for slot_name, state in snapshot.items():
            value = state.value
            if isinstance(value, Enum):
                value = str(value)
            formatted.append(
                f"{slot_name}=({state.status}, value={value!r}, confidence={state.confidence})"
            )
        return "; ".join(formatted)

    def _format_proposed_actions(self, actions: list[ProposedAction]) -> str:
        if not actions:
            return "- No deterministic slot actions detected. Ask only for missing or tentative required slots."

        lines = []
        same_turn_tentative_slots: list[str] = []
        for index, action in enumerate(actions, start=1):
            if action.action_type == ProposedActionType.RECORD:
                lines.append(
                    "- "
                    f"{index}. call record_slot_candidate(slot_name={action.slot_name!r}, "
                    f"value={action.value!r}, confidence={action.confidence:.2f}, "
                    f"confirmed={action.confirmed}) because {action.reason}"
                )
                if not action.confirmed:
                    same_turn_tentative_slots.append(action.slot_name)
            else:
                lines.append(
                    "- "
                    f"{index}. call confirm_slot(slot_name={action.slot_name!r}, "
                    f"value={action.value!r}) because {action.reason}"
                )

        if same_turn_tentative_slots:
            labels = ", ".join(
                self._slot_prompt_label(slot_name)
                for slot_name in same_turn_tentative_slots
            )
            lines.append(
                "- Do NOT call confirm_slot for these values on this same turn because they were just "
                f"recorded as tentative and still need explicit caller confirmation: {labels}."
            )

        predicted_snapshot = self._snapshot_after_actions(actions)
        if (
            self._all_required_confirmed_for_snapshot(predicted_snapshot)
            and not self._completion_requested
        ):
            lines.append(
                "- After tool calls, call complete_intake() before your assistant message."
            )
        else:
            lines.append(
                "- After tool calls, do not call complete_intake unless every currently required slot "
                "is confirmed in structured state."
            )
        return "\n".join(lines)

    def _build_response_requirements(self, actions: list[ProposedAction]) -> str:
        predicted_snapshot = self._snapshot_after_actions(actions)
        required_slots = self._required_slots_for_snapshot(predicted_snapshot)
        missing_slots = [
            slot_name
            for slot_name in required_slots
            if predicted_snapshot.get(slot_name, SlotState()).status == SlotStatus.EMPTY
        ]
        tentative_slots = [
            slot_name
            for slot_name in required_slots
            if predicted_snapshot.get(slot_name, SlotState()).status
            == SlotStatus.FILLED
        ]

        acknowledgements: list[str] = []
        for action in actions:
            label = self._slot_prompt_label(action.slot_name)
            value = action.value
            if action.slot_name == "issue_category":
                acknowledgements.append(f"{label} ({value})")
            elif action.slot_name == "phone_number":
                acknowledgements.append(f"{label} ({value})")
            else:
                acknowledgements.append(f"{label} ({value})")

        lines = []
        if acknowledgements:
            details = ", ".join(dict.fromkeys(acknowledgements))
            lines.append(
                "- In your first sentence, explicitly acknowledge EVERY detail captured from this turn: "
                f"{details}."
            )

        if tentative_slots:
            labels = ", ".join(
                self._slot_prompt_label(slot_name) for slot_name in tentative_slots
            )
            lines.append(
                f"- Do NOT say intake is complete. Explicitly ask the caller to confirm every tentative required slot: {labels}."
            )

        if missing_slots:
            labels = ", ".join(
                self._slot_prompt_label(slot_name) for slot_name in missing_slots
            )
            lines.append(
                "- Ask for ALL still-missing required slots in the same reply, not just one of them: "
                f"{labels}."
            )

        if not missing_slots and not tentative_slots:
            issue_slot = predicted_snapshot.get("issue_category")
            issue_text = None
            if issue_slot and issue_slot.value is not None:
                issue_text = str(issue_slot.value)
            if any(
                action.action_type == ProposedActionType.CONFIRM for action in actions
            ):
                lines.append(
                    "- Explicitly say the previously tentative details are now confirmed and intake is complete."
                )
            else:
                lines.append(
                    "- State clearly that intake is complete only now that all required details are confirmed."
                )
            if issue_text:
                lines.append(
                    f"- Summarize the captured problem succinctly using the issue category {issue_text}."
                )

        lines.append("- Do not re-ask for any slot that is already confirmed.")
        return "\n".join(lines)

    def _snapshot_after_actions(
        self, actions: list[ProposedAction]
    ) -> dict[str, SlotState]:
        snapshot = self._tracker.snapshot()
        for action in actions:
            state = snapshot.setdefault(action.slot_name, SlotState())
            coerced_value = self._coerce_slot_value(action.slot_name, action.value)
            if action.action_type == ProposedActionType.CONFIRM or action.confirmed:
                state.status = SlotStatus.CONFIRMED
                state.value = coerced_value
                state.confidence = None
            else:
                state.status = SlotStatus.FILLED
                state.value = coerced_value
                state.confidence = action.confidence
        return snapshot

    def _required_slots_for_snapshot(self, snapshot: dict[str, SlotState]) -> list[str]:
        issue_slot = snapshot.get("issue_category")
        issue_category: IssueCategory | None = None
        if issue_slot and issue_slot.value is not None:
            issue_category = (
                issue_slot.value
                if isinstance(issue_slot.value, IssueCategory)
                else self._parse_issue_category(str(issue_slot.value))
            )

        mode = (
            IntakeMode.DANGER_MINIMUM
            if self._classification.danger_type != DangerType.NONE
            else self._mode
        )
        address_relevant = self._classification.address_relevant
        if issue_category is not None:
            address_relevant = None

        return get_required_slots(
            mode=mode,
            address_relevant=address_relevant,
            danger_type=self._classification.danger_type,
            issue_category=issue_category,
        )

    def _all_required_confirmed_for_snapshot(
        self, snapshot: dict[str, SlotState]
    ) -> bool:
        required_slots = self._required_slots_for_snapshot(snapshot)
        return all(
            snapshot.get(slot_name, SlotState()).status == SlotStatus.CONFIRMED
            for slot_name in required_slots
        )

    def _slot_prompt_label(self, slot_name: str) -> str:
        labels = {
            "customer_name": "customer name",
            "phone_number": "callback number",
            "service_address": "service address",
            "issue_category": "reported issue",
        }
        return labels.get(slot_name, slot_name.replace("_", " "))

    def _extract_phone_number(self, transcript: str) -> str | None:
        match = _PHONE_RE.search(transcript)
        if match is None:
            return None
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    def _extract_name(self, transcript: str) -> tuple[str, bool] | None:
        match = _NAME_RE.search(transcript)
        if match is None:
            return None

        name = re.sub(r"\s+", " ", match.group("name")).strip(" ,.")
        if not name:
            return None
        tentative = bool(match.group("tentative"))
        return name, tentative

    def _extract_address(self, transcript: str) -> tuple[str, bool] | None:
        match = _ADDRESS_RE.search(transcript)
        if match is None:
            return None

        address = re.sub(r"\s+", " ", match.group("address")).strip(" ,.")
        if not address:
            return None
        tentative = match.group("prefix").casefold().startswith("i think")
        return address, tentative

    def _has_confirmation_cue(self, transcript: str) -> bool:
        return bool(_CONFIRMATION_RE.search(transcript))
