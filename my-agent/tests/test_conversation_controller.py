from __future__ import annotations

import pytest
from livekit.agents import AgentSession, inference, llm

from conversation.conversation_controller import HVACConversationController


@pytest.fixture
def llm_model() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.mark.asyncio
async def test_controller_opens_as_after_hours_hvac_assistant(
    llm_model: llm.LLM,
) -> None:
    async with llm_model as model, AgentSession(llm=model) as session:
        await session.start(HVACConversationController())

        result = await session.run(user_input="Hello")

        await (
            result.expect.next_event(type="message").judge(
                model,
                intent=(
                    "Greets the caller as North Star HVAC's after-hours line, offers help with the "
                    "caller’s heating or cooling issue, and asks for intake details without claiming "
                    "to be a generic AI assistant."
                ),
            )
        )
        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_controller_emits_explicit_handoff_event_for_danger_keywords(
    llm_model: llm.LLM,
) -> None:
    async with llm_model as model, AgentSession(llm=model) as session:
        await session.start(HVACConversationController())

        result = await session.run(
            user_input=(
                "I smell gas by the furnace and I feel dizzy. My name is Sam and my number is "
                "416-555-0144."
            )
        )

        handoff_event = result.expect.contains_agent_handoff().event()
        assert handoff_event.new_agent.__class__.__name__ == "SafetyAgent"
        assert handoff_event.item.type == "agent_handoff"
        assert handoff_event.old_agent is not None
        await (
            result.expect.contains_message(role="assistant").judge(
                model,
                intent=(
                    "Tells the caller to treat the situation as an emergency first, advises them to "
                    "leave the area and contact emergency help, and only then attempts minimum "
                    "viable capture such as name and callback number if it is safe to do so."
                ),
            )
        )


@pytest.mark.asyncio
async def test_controller_closes_cleanly_after_normal_intake_completion(
    llm_model: llm.LLM,
) -> None:
    async with llm_model as model, AgentSession(llm=model) as session:
        await session.start(HVACConversationController())

        result = await session.run(
            user_input=(
                "Hi, my name is Taylor, my callback number is 416-555-0188, the furnace has no "
                "heat, and the address is 88 Queen Street West in Toronto."
            )
        )

        result.expect.next_event(type="function_call")
        result.expect.next_event(type="function_call")
        result.expect.next_event(type="function_call")
        result.expect.next_event(type="function_call")
        result.expect.next_event(type="function_call")
        await (
            result.expect.next_event(type="message").judge(
                model,
                intent=(
                    "Confirms the normal HVAC intake is complete only after the required details were "
                    "captured, closes the call concisely, and gives a clean next-step expectation "
                    "without reopening slot collection or weakening the deterministic S02 completion semantics."
                ),
            )
        )
        result.expect.no_more_events()
