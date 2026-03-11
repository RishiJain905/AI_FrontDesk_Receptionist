"""Rule-first live transcript classification for HVAC intake."""

from __future__ import annotations

from dataclasses import dataclass

from config.hvac_demo_config import HVAC_DEMO_CONFIG
from hvac_types.business_config import BusinessConfig
from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel

from classification.rules import (
    detect_address_relevance,
    detect_danger,
    detect_issue_category,
    detect_urgency,
)


@dataclass(frozen=True)
class LiveClassification:
    """Stable classifier output for tests and downstream intake policy."""

    danger_type: DangerType
    urgency_level: UrgencyLevel
    issue_category: IssueCategory
    address_relevant: bool
    matched_keywords: tuple[str, ...]

    @property
    def danger_detected(self) -> bool:
        return self.danger_type != DangerType.NONE


class LiveClassifier:
    """Deterministic classifier backed by config-provided keyword seeds."""

    def __init__(self, config: BusinessConfig = HVAC_DEMO_CONFIG) -> None:
        self._config = config

    def classify(self, transcript: str) -> LiveClassification:
        danger_type, danger_matches = detect_danger(
            transcript,
            safety_keywords=self._config.safety_keywords,
        )
        issue_category, issue_matches = detect_issue_category(
            transcript,
            no_heat_keywords=self._config.no_heat_keywords,
            no_cool_keywords=self._config.no_cool_keywords,
        )
        if danger_type != DangerType.NONE and issue_category == IssueCategory.BAD_SMELL:
            issue_category = IssueCategory.OTHER
            issue_matches = ()

        urgency_level = detect_urgency(
            transcript,
            danger_type=danger_type,
            issue_category=issue_category,
        )
        address_relevant = detect_address_relevance(
            transcript,
            danger_type=danger_type,
            issue_category=issue_category,
        )

        ordered_keywords = tuple(dict.fromkeys((*danger_matches, *issue_matches)))
        return LiveClassification(
            danger_type=danger_type,
            urgency_level=urgency_level,
            issue_category=issue_category,
            address_relevant=address_relevant,
            matched_keywords=ordered_keywords,
        )
