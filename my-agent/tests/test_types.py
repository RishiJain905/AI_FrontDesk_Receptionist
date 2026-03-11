"""Tests for hvac_types enums and slot state dataclass.

These tests verify:
- Enums are importable and have correct str values
- SlotState initializes cleanly with defaults
- SlotStatus enum membership
"""

from __future__ import annotations

import pytest

from config.hvac_demo_config import HVAC_DEMO_CONFIG
from config.load_config import load_config
from hvac_types.business_config import BusinessConfig
from hvac_types.call_intake_record import CallIntakeRecord, CallStatus
from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel
from hvac_types.slot_state import SlotState, SlotStatus


class TestIssueCategory:
    """Tests for the IssueCategory enum."""

    def test_is_string_enum(self):
        assert isinstance(IssueCategory.NO_HEAT, str)

    def test_no_heat_value(self):
        assert IssueCategory.NO_HEAT == "no_heat"

    def test_no_cool_value(self):
        assert IssueCategory.NO_COOL == "no_cool"

    def test_poor_airflow_value(self):
        assert IssueCategory.POOR_AIRFLOW == "poor_airflow"

    def test_strange_noise_value(self):
        assert IssueCategory.STRANGE_NOISE == "strange_noise"

    def test_bad_smell_value(self):
        assert IssueCategory.BAD_SMELL == "bad_smell"

    def test_leaking_water_value(self):
        assert IssueCategory.LEAKING_WATER == "leaking_water"

    def test_system_short_cycling_value(self):
        assert IssueCategory.SYSTEM_SHORT_CYCLING == "system_short_cycling"

    def test_thermostat_unresponsive_value(self):
        assert IssueCategory.THERMOSTAT_UNRESPONSIVE == "thermostat_unresponsive"

    def test_other_value(self):
        assert IssueCategory.OTHER == "other"

    def test_str_representation(self):
        assert str(IssueCategory.NO_HEAT) == "no_heat"

    def test_all_members_importable(self):
        # Confirm expected members exist
        members = [e.value for e in IssueCategory]
        assert "no_heat" in members
        assert "no_cool" in members
        assert "other" in members


class TestUrgencyLevel:
    """Tests for the UrgencyLevel enum."""

    def test_is_string_enum(self):
        assert isinstance(UrgencyLevel.ROUTINE, str)

    def test_routine_value(self):
        assert UrgencyLevel.ROUTINE == "routine"

    def test_urgent_value(self):
        assert UrgencyLevel.URGENT == "urgent"

    def test_emergency_value(self):
        assert UrgencyLevel.EMERGENCY == "emergency"

    def test_unknown_value(self):
        assert UrgencyLevel.UNKNOWN == "unknown"

    def test_str_representation(self):
        assert str(UrgencyLevel.EMERGENCY) == "emergency"


class TestDangerType:
    """Tests for the DangerType enum."""

    def test_is_string_enum(self):
        assert isinstance(DangerType.NONE, str)

    def test_none_value(self):
        assert DangerType.NONE == "none"

    def test_gas_leak_value(self):
        assert DangerType.GAS_LEAK == "gas_leak"

    def test_carbon_monoxide_value(self):
        assert DangerType.CARBON_MONOXIDE == "carbon_monoxide"

    def test_electrical_hazard_value(self):
        assert DangerType.ELECTRICAL_HAZARD == "electrical_hazard"

    def test_flooding_value(self):
        assert DangerType.FLOODING == "flooding"

    def test_str_representation(self):
        assert str(DangerType.GAS_LEAK) == "gas_leak"


class TestSlotStatus:
    """Tests for the SlotStatus enum."""

    def test_is_string_enum(self):
        assert isinstance(SlotStatus.EMPTY, str)

    def test_empty_value(self):
        assert SlotStatus.EMPTY == "empty"

    def test_filled_value(self):
        assert SlotStatus.FILLED == "filled"

    def test_confirmed_value(self):
        assert SlotStatus.CONFIRMED == "confirmed"

    def test_str_representation(self):
        assert str(SlotStatus.FILLED) == "filled"


class TestBusinessConfig:
    """Tests for BusinessConfig dataclass defaults and list isolation."""

    def test_defaults_to_none_and_empty_lists(self):
        cfg = BusinessConfig()
        assert cfg.business_name is None
        assert cfg.business_phone is None
        assert cfg.owner_phone is None
        assert cfg.timezone is None
        assert cfg.service_area is None
        assert cfg.emergency_instructions is None
        assert cfg.after_hours_start is None
        assert cfg.after_hours_end is None
        assert cfg.safety_keywords == []
        assert cfg.no_heat_keywords == []
        assert cfg.no_cool_keywords == []
        assert cfg.dispatcher_contacts == []

    def test_list_defaults_are_independent_between_instances(self):
        cfg1 = BusinessConfig()
        cfg2 = BusinessConfig()

        cfg1.safety_keywords.append("gas")
        cfg1.no_heat_keywords.append("furnace")
        cfg1.no_cool_keywords.append("ac")
        cfg1.dispatcher_contacts.append("+1-555-0100")

        assert cfg2.safety_keywords == []
        assert cfg2.no_heat_keywords == []
        assert cfg2.no_cool_keywords == []
        assert cfg2.dispatcher_contacts == []

    def test_accepts_after_hours_window_fields(self):
        cfg = BusinessConfig(
            after_hours_start="17:00",
            after_hours_end="09:00",
        )

        assert cfg.after_hours_start == "17:00"
        assert cfg.after_hours_end == "09:00"


class TestLoadConfig:
    """Tests for runtime config validation and default demo profile."""

    @pytest.mark.parametrize(
        "missing_field", ["business_name", "timezone", "owner_phone"]
    )
    def test_raises_value_error_for_none_required_fields(self, missing_field: str):
        cfg = BusinessConfig(
            business_name="North Star HVAC",
            timezone="America/Toronto",
            owner_phone="+1-416-555-0110",
        )
        setattr(cfg, missing_field, None)

        with pytest.raises(ValueError, match=missing_field):
            load_config(cfg)

    @pytest.mark.parametrize(
        "missing_field", ["business_name", "timezone", "owner_phone"]
    )
    def test_raises_value_error_for_empty_required_fields(self, missing_field: str):
        cfg = BusinessConfig(
            business_name="North Star HVAC",
            timezone="America/Toronto",
            owner_phone="+1-416-555-0110",
        )
        setattr(cfg, missing_field, "")

        with pytest.raises(ValueError, match=missing_field):
            load_config(cfg)

    def test_returns_demo_config_when_no_config_is_passed(self):
        loaded = load_config()

        assert loaded is HVAC_DEMO_CONFIG

    def test_demo_config_passes_validation(self):
        loaded = load_config(HVAC_DEMO_CONFIG)

        assert loaded is HVAC_DEMO_CONFIG

    def test_demo_config_exposes_default_after_hours_window(self):
        assert HVAC_DEMO_CONFIG.after_hours_start == "17:00"
        assert HVAC_DEMO_CONFIG.after_hours_end == "09:00"

    @pytest.mark.parametrize("window_field", ["after_hours_start", "after_hours_end"])
    def test_raises_value_error_for_missing_after_hours_fields(self, window_field: str):
        cfg = BusinessConfig(
            business_name="North Star HVAC",
            timezone="America/Toronto",
            owner_phone="+1-416-555-0110",
            after_hours_start="17:00",
            after_hours_end="09:00",
        )
        setattr(cfg, window_field, None)

        with pytest.raises(ValueError, match=window_field):
            load_config(cfg)

    @pytest.mark.parametrize("window_field", ["after_hours_start", "after_hours_end"])
    def test_raises_value_error_for_blank_after_hours_fields(self, window_field: str):
        cfg = BusinessConfig(
            business_name="North Star HVAC",
            timezone="America/Toronto",
            owner_phone="+1-416-555-0110",
            after_hours_start="17:00",
            after_hours_end="09:00",
        )
        setattr(cfg, window_field, "   ")

        with pytest.raises(ValueError, match=window_field):
            load_config(cfg)

    @pytest.mark.parametrize(
        ("window_field", "value"),
        [
            ("after_hours_start", "5pm"),
            ("after_hours_end", "24:00"),
        ],
    )
    def test_raises_value_error_for_unparseable_after_hours_fields(
        self,
        window_field: str,
        value: str,
    ):
        cfg = BusinessConfig(
            business_name="North Star HVAC",
            timezone="America/Toronto",
            owner_phone="+1-416-555-0110",
            after_hours_start="17:00",
            after_hours_end="09:00",
        )
        setattr(cfg, window_field, value)

        with pytest.raises(ValueError, match=window_field):
            load_config(cfg)


class TestCallStatus:
    """Tests for the CallStatus enum."""

    def test_is_string_enum(self):
        assert isinstance(CallStatus.PARTIAL, str)

    def test_partial_value(self):
        assert CallStatus.PARTIAL == "partial"

    def test_complete_value(self):
        assert CallStatus.COMPLETE == "complete"

    def test_str_representation(self):
        assert str(CallStatus.COMPLETE) == "complete"


class TestCallIntakeRecord:
    """Tests for CallIntakeRecord dataclass defaults."""

    def test_defaults_all_fields_to_none(self):
        record = CallIntakeRecord()
        assert record.call_status is None
        assert record.customer_name is None
        assert record.phone_number is None
        assert record.service_address is None
        assert record.issue_category is None
        assert record.urgency_level is None
        assert record.danger_type is None
        assert record.has_pets is None
        assert record.is_someone_home is None
        assert record.callback_requested is None
        assert record.callback_number_confirmed is None
        assert record.caller_id is None
        assert record.summary is None
        assert record.notes is None
        assert record.callback_time is None
        assert record.customer_type is None
        assert record.transcript is None
        assert record.ai_summary is None
        assert record.notify_owner is None
        assert record.sms_sent is None

    def test_accepts_optional_integration_fields(self):
        record = CallIntakeRecord(
            callback_time="Tomorrow after 8 AM",
            customer_type="existing",
            callback_number_confirmed=False,
            caller_id="+1-416-555-0144",
            transcript="Caller says the furnace stopped overnight.",
            ai_summary="Existing customer with an urgent no-heat outage.",
            notify_owner=True,
            sms_sent=False,
        )

        assert record.callback_time == "Tomorrow after 8 AM"
        assert record.customer_type == "existing"
        assert record.callback_number_confirmed is False
        assert record.caller_id == "+1-416-555-0144"
        assert record.transcript == "Caller says the furnace stopped overnight."
        assert record.ai_summary == "Existing customer with an urgent no-heat outage."
        assert record.notify_owner is True
        assert record.sms_sent is False


class TestSlotState:
    """Tests for the SlotState dataclass."""

    def test_default_initialization(self):
        slot = SlotState()
        assert slot.status == SlotStatus.EMPTY
        assert slot.value is None
        assert slot.confidence is None
        assert slot.attempts == 0

    def test_filled_initialization(self):
        slot = SlotState(
            status=SlotStatus.FILLED,
            value="no_heat",
            confidence=0.95,
            attempts=1,
        )
        assert slot.status == SlotStatus.FILLED
        assert slot.value == "no_heat"
        assert slot.confidence == 0.95
        assert slot.attempts == 1

    def test_status_is_slot_status_type(self):
        slot = SlotState()
        assert isinstance(slot.status, SlotStatus)

    def test_multiple_instances_are_independent(self):
        slot1 = SlotState()
        slot2 = SlotState()
        slot1.attempts = 3
        # Dataclasses should not share state
        assert slot2.attempts == 0

    def test_confirmed_status(self):
        slot = SlotState(
            status=SlotStatus.CONFIRMED, value="urgent", confidence=1.0, attempts=2
        )
        assert slot.status == SlotStatus.CONFIRMED
        assert slot.value == "urgent"
