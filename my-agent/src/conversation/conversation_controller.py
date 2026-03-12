"""After-hours HVAC conversation controller with explicit safety handoff."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from livekit.agents import function_tool, llm
from livekit.agents.voice.generation import update_instructions

from classification.live_classifier import LiveClassification, LiveClassifier
from config.hvac_demo_config import HVAC_DEMO_CONFIG
from conversation.intake_policy import IntakeMode, get_required_slots
from conversation.intake_task import IntakeTask, IntakeTaskResult
from conversation.prompts import (
    CLOSING_INSTRUCTIONS,
    SAFETY_INSTRUCTIONS,
    build_system_prompt,
)
from hvac_types.business_config import BusinessConfig


@dataclass(frozen=True)
class HandoffState:
    """Inspectable safety handoff state for tests and diagnostics."""

    reason: str
    classification: LiveClassification
    previous_mode: str
    current_mode: str = "safety"


_GREETING_ONLY_RE = re.compile(
    r"^(?:hi|hello|hey|good\s+(?:morning|afternoon|evening)|good day)[!. ]*$",
    flags=re.IGNORECASE,
)


class SafetyAgent(IntakeTask):
    """Danger-mode intake that keeps emergency guidance first and intake minimal."""

    def __init__(
        self,
        *,
        config: BusinessConfig = HVAC_DEMO_CONFIG,
        classifier: LiveClassifier | None = None,
        classification: LiveClassification | None = None,
        handoff_reason: str | None = None,
        chat_ctx: llm.ChatContext | None = None,
    ) -> None:
        self.config = config
        self.classifier = classifier or LiveClassifier(config=config)
        self.latest_classification = classification or self.classifier.classify("")
        self.current_mode = "safety"
        self.handoff_reason = handoff_reason or "danger_detected"
        self.handoff_state = HandoffState(
            reason=self.handoff_reason,
            classification=self.latest_classification,
            previous_mode="normal",
        )
        super().__init__(
            classifier=self.classifier,
            mode=IntakeMode.DANGER_MINIMUM,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        mutable_chat_ctx = self.chat_ctx.copy()
        mutable_chat_ctx.add_message(
            role="assistant",
            content=(
                "Safety mode is now active. Your very next spoken reply must calmly say this may be an emergency, "
                "tell the caller to leave the area and call 911 first, and only then ask for the minimum callback details if it is safe."
            ),
        )
        await self.update_chat_ctx(mutable_chat_ctx)
        await self.update_instructions(self._build_safety_instructions())

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ) -> None:
        await super().on_user_turn_completed(turn_ctx, new_message)
        self.latest_classification = self._classification
        await self.update_instructions(self._build_safety_instructions())

    def _build_safety_instructions(self) -> str:
        required_slots = get_required_slots(
            mode=IntakeMode.DANGER_MINIMUM,
            danger_type=self.latest_classification.danger_type,
            issue_category=self._slot_issue_category(),
        )
        return "\n\n".join(
            [
                build_system_prompt(self.config),
                SAFETY_INSTRUCTIONS,
                CLOSING_INSTRUCTIONS,
                super()._build_instructions(),
                (
                    "Safety-mode requirements:\n"
                    f"- Current mode: {self.current_mode}.\n"
                    f"- Handoff reason: {self.handoff_reason}.\n"
                    f"- Minimum required slots in safety mode: {', '.join(required_slots)}.\n"
                    "- Your first spoken reply in this mode must give calm emergency guidance before any intake question.\n"
                    "- After the emergency guidance, ask only for the minimum viable details still required for a callback.\n"
                    "- Do not return to the full normal intake flow unless a future controller explicitly changes agents."
                ),
            ]
        )


class HVACIntakeAgent(IntakeTask):
    """Normal-mode intake agent that stays thin over IntakeTask and hands off on danger."""

    def __init__(
        self,
        *,
        config: BusinessConfig = HVAC_DEMO_CONFIG,
        classifier: LiveClassifier | None = None,
        chat_ctx: llm.ChatContext | None = None,
    ) -> None:
        self.config = config
        self.classifier = classifier or LiveClassifier(config=config)
        self.current_mode = "normal"
        self.latest_classification = self.classifier.classify("")
        self.handoff_reason: str | None = None
        self.handoff_state: HandoffState | None = None
        self.last_completed_intake_summary: IntakeTaskResult | None = None
        super().__init__(
            classifier=self.classifier,
            mode=IntakeMode.NORMAL,
            chat_ctx=chat_ctx,
        )
        self._normal_tools = self.tools
        self._handoff_only_tools = [
            tool
            for tool in self._normal_tools
            if getattr(tool.info, "name", None) == "handoff_to_safety"
        ]

    async def on_enter(self) -> None:
        await self.update_tools(self._normal_tools)
        await self.update_instructions(self._build_controller_instructions())

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ) -> None:
        transcript = (new_message.text_content or "").strip()
        self.latest_classification = self.classifier.classify(transcript)

        if self.latest_classification.danger_detected:
            matched = ", ".join(self.latest_classification.matched_keywords) or "danger"
            reason = f"danger_detected:{matched}"
            self.handoff_reason = reason
            self.handoff_state = HandoffState(
                reason=reason,
                classification=self.latest_classification,
                previous_mode=self.current_mode,
            )
            self.current_mode = "safety"
            await self.update_tools(self._handoff_only_tools)
            await self.update_instructions(self._build_danger_handoff_instructions())
            return

        if self._is_greeting_only_turn(transcript):
            await self.update_tools([])
            await self.update_instructions(self._build_greeting_only_instructions())
            return

        await self.update_tools(self._normal_tools)
        await super().on_user_turn_completed(turn_ctx, new_message)
        self.latest_classification = self._classification
        if self.done():
            self.last_completed_intake_summary = self.result
        await self.update_instructions(self._build_controller_instructions())

    def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool],
        model_settings: Any,
    ):
        transcript = self._latest_user_transcript(chat_ctx)
        self.latest_classification = self.classifier.classify(transcript)

        if self.latest_classification.danger_detected:
            matched = ", ".join(self.latest_classification.matched_keywords) or "danger"
            reason = f"danger_detected:{matched}"
            self.handoff_reason = reason
            self.handoff_state = HandoffState(
                reason=reason,
                classification=self.latest_classification,
                previous_mode=self.current_mode,
            )
            self.current_mode = "safety"
            update_instructions(
                chat_ctx,
                instructions=self._build_danger_handoff_instructions(),
                add_if_missing=True,
            )
            return super().llm_node(chat_ctx, self._handoff_only_tools, model_settings)

        self.current_mode = "normal"
        self.handoff_reason = None
        self.handoff_state = None
        if self._is_greeting_only_turn(transcript):
            update_instructions(
                chat_ctx,
                instructions=self._build_greeting_only_instructions(),
                add_if_missing=True,
            )
            return super().llm_node(chat_ctx, [], model_settings)

        update_instructions(
            chat_ctx,
            instructions=self._build_controller_instructions(),
            add_if_missing=True,
        )
        return super().llm_node(chat_ctx, self._normal_tools, model_settings)

    @function_tool()
    async def handoff_to_safety(self) -> tuple[SafetyAgent, str]:
        """Transfer the live call to the dedicated safety agent when danger is detected."""

        matched = ", ".join(self.latest_classification.matched_keywords) or "danger"
        reason = self.handoff_reason or f"danger_detected:{matched}"
        self.handoff_reason = reason
        if self.handoff_state is None:
            self.handoff_state = HandoffState(
                reason=reason,
                classification=self.latest_classification,
                previous_mode="normal",
            )
        self.current_mode = "safety"
        return (
            SafetyAgent(
                config=self.config,
                classifier=self.classifier,
                classification=self.latest_classification,
                handoff_reason=reason,
                chat_ctx=self.chat_ctx,
            ),
            "Safety handoff complete. Continue with emergency-first guidance and minimum callback capture only if safe.",
        )

    def _latest_user_transcript(self, chat_ctx: llm.ChatContext) -> str:
        for item in reversed(chat_ctx.items):
            if item.type == "message" and item.role == "user":
                return item.text_content or ""
        return ""

    def _is_greeting_only_turn(self, transcript: str) -> bool:
        normalized = transcript.strip()
        return bool(normalized) and bool(_GREETING_ONLY_RE.fullmatch(normalized))

    def _build_greeting_only_instructions(self) -> str:
        return "\n\n".join(
            [
                build_system_prompt(self.config),
                CLOSING_INSTRUCTIONS,
                (
                    "Greeting-only turn handling:\n"
                    "- The caller only greeted the line and has not provided reliable intake data yet.\n"
                    "- Do not call any intake tools for this turn.\n"
                    "- Do not infer the caller's name, phone number, issue, or address from the greeting.\n"
                    "- Reply with a natural business-specific after-hours HVAC greeting and then ask for the caller's name, callback number, and heating or cooling issue."
                ),
            ]
        )

    def _build_controller_instructions(self) -> str:
        return "\n\n".join(
            [
                build_system_prompt(self.config),
                CLOSING_INSTRUCTIONS,
                super()._build_instructions(),
                (
                    "Controller state:\n"
                    f"- Current mode: {self.current_mode}.\n"
                    f"- Latest danger type: {self.latest_classification.danger_type}.\n"
                    f"- Latest issue category: {self.latest_classification.issue_category}.\n"
                    f"- Handoff reason: {self.handoff_reason or '<none>'}.\n"
                    "- On a normal first turn, greet the caller with a business-specific dispatcher voice such as 'North Star HVAC after-hours dispatch' or 'you've reached North Star HVAC's overnight service line.'\n"
                    "- Sound like a real overnight HVAC dispatcher, not an AI assistant, generic helper, or template bot.\n"
                    "- If the latest danger type is not none, do not continue normal intake. Call handoff_to_safety immediately before any assistant message so the runtime emits an explicit agent handoff.\n"
                    "- Stay in normal intake unless live danger classification requires an explicit safety handoff."
                ),
            ]
        )

    def _build_danger_handoff_instructions(self) -> str:
        matched = ", ".join(self.latest_classification.matched_keywords) or "danger"
        return "\n\n".join(
            [
                build_system_prompt(self.config),
                SAFETY_INSTRUCTIONS,
                (
                    "Immediate controller action required:\n"
                    f"- Current mode: {self.current_mode}.\n"
                    f"- Danger type: {self.latest_classification.danger_type}.\n"
                    f"- Matched keywords: {matched}.\n"
                    f"- Handoff reason: {self.handoff_reason or '<none>'}.\n"
                    "- Do not call any intake tools on this turn.\n"
                    "- Call handoff_to_safety immediately and nothing else so the runtime can transfer control.\n"
                    "- After the handoff, the SafetyAgent will deliver the emergency-first reply and collect only minimum viable details."
                ),
            ]
        )


class HVACConversationController(HVACIntakeAgent):
    """Public controller surface used by tests and the entrypoint."""

    pass
