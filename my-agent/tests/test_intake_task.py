from __future__ import annotations

import pytest
from livekit.agents import AgentSession, inference, llm

from conversation.intake_task import IntakeTask


def assert_next_function_call(expectation, *names: str) -> None:
    event = expectation.next_event(type="function_call").event()
    assert event.item.name in set(names)


@pytest.fixture
def llm_model() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.mark.asyncio
async def test_partial_volunteer_flow_only_asks_for_remaining_required_slots(
    llm_model: llm.LLM,
) -> None:
    async with llm_model as model, AgentSession(llm=model) as session:
        await session.start(IntakeTask())

        result = await session.run(
            user_input=(
                "Hi, this is Taylor. My number is 416-555-0188 and the furnace has no heat."
            )
        )

        assert_next_function_call(result.expect, "record_slot_candidate")
        assert_next_function_call(result.expect, "record_slot_candidate")
        assert_next_function_call(result.expect, "record_slot_candidate")
        await (
            result.expect.next_event(type="message")
            .judge(
                model,
                intent=(
                    "Acknowledges the volunteered name, phone number, and no-heat issue, "
                    "and asks for the still-missing service address without re-asking for "
                    "name or phone number."
                ),
            )
        )
        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_tentative_slot_requires_explicit_confirmation_before_completion(
    llm_model: llm.LLM,
) -> None:
    async with llm_model as model, AgentSession(llm=model) as session:
        await session.start(IntakeTask())

        first_turn = await session.run(
            user_input=(
                "My name is maybe Chris, my number is 416-555-0111, and I think the address "
                "is 14 King Street. The AC is not working."
            )
        )

        assert_next_function_call(first_turn.expect, "record_slot_candidate")
        assert_next_function_call(first_turn.expect, "record_slot_candidate")
        assert_next_function_call(first_turn.expect, "record_slot_candidate")
        assert_next_function_call(first_turn.expect, "record_slot_candidate")
        await (
            first_turn.expect.next_event(type="message")
            .judge(
                model,
                intent=(
                    "Does not mark intake complete. Explicitly asks the caller to confirm the "
                    "tentative customer name and/or service address before proceeding."
                ),
            )
        )
        first_turn.expect.no_more_events()

        second_turn = await session.run(
            user_input=(
                "Yes, my name is Chris and yes, the address is 14 King Street, Toronto."
            )
        )

        assert_next_function_call(
            second_turn.expect,
            "confirm_slot",
            "record_slot_candidate",
        )
        assert_next_function_call(
            second_turn.expect,
            "confirm_slot",
            "record_slot_candidate",
        )
        assert_next_function_call(second_turn.expect, "complete_intake")
        await (
            second_turn.expect.next_event(type="message")
            .judge(
                model,
                intent=(
                    "Confirms intake is now complete after the caller confirmed the pending "
                    "details, and summarizes the captured problem succinctly."
                ),
            )
        )
        second_turn.expect.no_more_events()


@pytest.mark.asyncio
async def test_completion_is_blocked_until_all_required_slots_are_confirmed(
    llm_model: llm.LLM,
) -> None:
    async with llm_model as model, AgentSession(llm=model) as session:
        await session.start(IntakeTask())

        first_turn = await session.run(
            user_input="My name is Morgan and I have no cooling at my house."
        )

        assert_next_function_call(first_turn.expect, "record_slot_candidate")
        assert_next_function_call(first_turn.expect, "record_slot_candidate")
        await (
            first_turn.expect.next_event(type="message")
            .judge(
                model,
                intent=(
                    "Does not complete the intake yet because the required callback number and "
                    "service address are still missing, and asks for the missing details."
                ),
            )
        )
        first_turn.expect.no_more_events()

        second_turn = await session.run(user_input="Sure, my callback number is 416-555-0199.")

        assert_next_function_call(second_turn.expect, "record_slot_candidate")
        await (
            second_turn.expect.next_event(type="message")
            .judge(
                model,
                intent=(
                    "Still does not complete intake because the service address remains required, "
                    "and specifically asks for the address."
                ),
            )
        )
        second_turn.expect.no_more_events()

        third_turn = await session.run(
            user_input="The address is 88 Queen Street West in Toronto."
        )

        assert_next_function_call(third_turn.expect, "record_slot_candidate")
        assert_next_function_call(third_turn.expect, "complete_intake")
        await (
            third_turn.expect.next_event(type="message")
            .judge(
                model,
                intent=(
                    "Completes intake only after all required slots are confirmed or otherwise "
                    "accepted by policy, and does not ask for already-collected information again."
                ),
            )
        )
        third_turn.expect.no_more_events()
