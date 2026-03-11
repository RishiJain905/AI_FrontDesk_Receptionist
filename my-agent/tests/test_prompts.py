from __future__ import annotations

from types import SimpleNamespace

from conversation.prompts import (
    CLOSING_INSTRUCTIONS,
    SAFETY_INSTRUCTIONS,
    build_system_prompt,
)


def test_build_system_prompt_identifies_after_hours_hvac_role() -> None:
    config = SimpleNamespace(
        business_name="North Star HVAC",
        assistant_name="Maya",
        dispatcher_name="North Star HVAC on-call tech",
        service_area="Toronto",
    )

    prompt = build_system_prompt(config)

    assert "North Star HVAC" in prompt
    assert "after-hours" in prompt.casefold()
    assert "HVAC" in prompt
    assert "Maya" in prompt
    assert "Toronto" in prompt
    assert "helpful voice AI assistant" not in prompt


def test_safety_instructions_require_emergency_first_guidance() -> None:
    assert "emergency" in SAFETY_INSTRUCTIONS.casefold()
    assert "911" in SAFETY_INSTRUCTIONS
    assert "gas" in SAFETY_INSTRUCTIONS.casefold() or "carbon monoxide" in SAFETY_INSTRUCTIONS.casefold()
    assert "before" in SAFETY_INSTRUCTIONS.casefold()
    assert "minimum" in SAFETY_INSTRUCTIONS.casefold() or "only" in SAFETY_INSTRUCTIONS.casefold()


def test_closing_instructions_require_concise_close_without_false_completion() -> None:
    assert "concise" in CLOSING_INSTRUCTIONS.casefold() or "brief" in CLOSING_INSTRUCTIONS.casefold()
    assert "do not" in CLOSING_INSTRUCTIONS.casefold()
    assert "complete" in CLOSING_INSTRUCTIONS.casefold()
    assert "next step" in CLOSING_INSTRUCTIONS.casefold() or "callback" in CLOSING_INSTRUCTIONS.casefold()
