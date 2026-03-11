from __future__ import annotations

import pytest

from config.hvac_demo_config import HVAC_DEMO_CONFIG
from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel
from hvac_types.slot_state import SlotStatus

from classification.live_classifier import LiveClassifier
from conversation.intake_policy import IntakeMode, get_required_slots
from conversation.slot_tracker import SlotTracker


class TestSlotTracker:
    def test_maps_empty_filled_confirmed_to_missing_tentative_confirmed_semantics(self):
        tracker = SlotTracker(required_slots=["customer_name", "service_address"])

        tracker.record_candidate("customer_name", "Pat", confidence=0.62)
        tracker.confirm("service_address", "123 Main St")

        snapshot = tracker.snapshot()

        assert snapshot["customer_name"].status == SlotStatus.FILLED
        assert snapshot["customer_name"].value == "Pat"
        assert snapshot["customer_name"].confidence == pytest.approx(0.62)
        assert snapshot["service_address"].status == SlotStatus.CONFIRMED
        assert snapshot["service_address"].value == "123 Main St"
        assert tracker.get_missing_slots() == []
        assert tracker.get_tentative_slots() == ["customer_name"]
        assert tracker.all_required_confirmed() is False

    def test_rejecting_a_candidate_clears_the_slot_back_to_missing(self):
        tracker = SlotTracker(required_slots=["issue_category"])

        tracker.record_candidate("issue_category", IssueCategory.NO_HEAT, confidence=0.51)
        tracker.reject("issue_category")

        snapshot = tracker.snapshot()

        assert snapshot["issue_category"].status == SlotStatus.EMPTY
        assert snapshot["issue_category"].value is None
        assert snapshot["issue_category"].confidence is None
        assert tracker.get_missing_slots() == ["issue_category"]
        assert tracker.get_tentative_slots() == []

    def test_confirming_a_tentative_slot_removes_it_from_tentative_and_missing_sets(self):
        tracker = SlotTracker(required_slots=["phone_number", "issue_category"])

        tracker.record_candidate("phone_number", "416-555-0100", confidence=0.58)
        tracker.record_candidate("issue_category", IssueCategory.NO_COOL, confidence=0.91)
        tracker.confirm("phone_number")
        tracker.confirm("issue_category")

        assert tracker.get_missing_slots() == []
        assert tracker.get_tentative_slots() == []
        assert tracker.all_required_confirmed() is True

    def test_all_required_confirmed_only_checks_the_required_subset(self):
        tracker = SlotTracker(required_slots=["customer_name", "issue_category"])

        tracker.confirm("customer_name", "Jordan")
        tracker.confirm("issue_category", IssueCategory.BAD_SMELL)
        tracker.record_candidate("service_address", "45 Queen St", confidence=0.45)

        assert tracker.all_required_confirmed() is True
        assert tracker.get_tentative_slots() == ["service_address"]


class TestIntakePolicy:
    def test_normal_mode_requires_core_contact_and_issue_slots(self):
        required = get_required_slots(mode=IntakeMode.NORMAL, address_relevant=True)

        assert required == [
            "customer_name",
            "phone_number",
            "service_address",
            "issue_category",
        ]

    def test_normal_mode_can_skip_address_when_classifier_marks_it_not_relevant(self):
        required = get_required_slots(mode=IntakeMode.NORMAL, address_relevant=False)

        assert required == ["customer_name", "phone_number", "issue_category"]

    def test_danger_minimum_mode_reduces_required_slots_but_keeps_callback_path(self):
        required = get_required_slots(mode=IntakeMode.DANGER_MINIMUM, address_relevant=True)

        assert required == ["customer_name", "phone_number", "issue_category"]
        assert "service_address" not in required


class TestLiveClassifier:
    def test_flags_gas_smell_as_danger_and_emergency(self):
        classifier = LiveClassifier(config=HVAC_DEMO_CONFIG)

        result = classifier.classify(
            "There is a gas smell near the furnace and the carbon monoxide alarm went off."
        )

        assert result.danger_type == DangerType.GAS_LEAK
        assert result.urgency_level == UrgencyLevel.EMERGENCY
        assert result.address_relevant is True
        assert "gas smell" in result.matched_keywords
        assert result.issue_category == IssueCategory.OTHER

    def test_flags_no_heat_with_elderly_parent_as_urgent(self):
        classifier = LiveClassifier(config=HVAC_DEMO_CONFIG)

        result = classifier.classify(
            "We have no heat tonight and my elderly mother is home with me."
        )

        assert result.issue_category == IssueCategory.NO_HEAT
        assert result.danger_type == DangerType.NONE
        assert result.urgency_level == UrgencyLevel.URGENT
        assert result.address_relevant is True
        assert "no heat" in result.matched_keywords

    def test_marks_address_not_relevant_for_callback_only_request(self):
        classifier = LiveClassifier(config=HVAC_DEMO_CONFIG)

        result = classifier.classify(
            "I just need to leave my number and get a callback about pricing tomorrow."
        )

        assert result.danger_type == DangerType.NONE
        assert result.urgency_level in {UrgencyLevel.ROUTINE, UrgencyLevel.UNKNOWN}
        assert result.address_relevant is False

    def test_detects_water_leak_and_flooding_hazard(self):
        classifier = LiveClassifier(config=HVAC_DEMO_CONFIG)

        result = classifier.classify(
            "The unit is leaking water and the basement is actively flooding around it."
        )

        assert result.issue_category == IssueCategory.LEAKING_WATER
        assert result.danger_type == DangerType.FLOODING
        assert result.urgency_level == UrgencyLevel.EMERGENCY
        assert result.address_relevant is True
