"""Deterministic transcript-classification rule helpers."""

from __future__ import annotations

from dataclasses import dataclass

from hvac_types.classification import DangerType, IssueCategory, UrgencyLevel


@dataclass(frozen=True)
class RuleMatch:
    """A stable, inspectable keyword rule match."""

    label: str
    matched_keywords: tuple[str, ...]


_GAS_KEYWORDS = ("gas leak", "gas smell", "smell gas", "gas")
_CO_KEYWORDS = ("carbon monoxide", "co alarm", "co detector", "co2 alarm")
_FLOODING_KEYWORDS = ("flooding", "flood", "actively flooding")
_ELECTRICAL_KEYWORDS = (
    "smoke",
    "sparks",
    "sparking",
    "electrical burning",
    "burning smell",
    "burning wire",
)
_LEAKING_WATER_KEYWORDS = (
    "leaking water",
    "water leak",
    "unit is leaking",
    "dripping water",
)
_BAD_SMELL_KEYWORDS = ("bad smell", "strange smell", "odor", "smell")
_ROUTINE_CALLBACK_KEYWORDS = (
    "callback",
    "call me back",
    "leave my number",
    "pricing",
    "quote",
    "estimate",
    "tomorrow",
)
_VULNERABILITY_KEYWORDS = (
    "elderly",
    "senior",
    "baby",
    "infant",
    "medical",
    "oxygen",
    "disabled",
)
_URGENT_SITUATION_KEYWORDS = ("tonight", "right now", "asap", "urgent")


def normalize_text(text: str) -> str:
    """Normalize transcript text for deterministic substring matching."""

    return " ".join(text.casefold().replace("-", " ").split())


def find_keywords(text: str, keywords: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Return matched keywords in the order supplied by the rule."""

    normalized = normalize_text(text)
    return tuple(
        keyword for keyword in keywords if normalize_text(keyword) in normalized
    )


def first_match(
    label: str, text: str, keywords: list[str] | tuple[str, ...]
) -> RuleMatch | None:
    """Return a rule match only when at least one keyword matched."""

    matched_keywords = find_keywords(text, keywords)
    if not matched_keywords:
        return None
    return RuleMatch(label=label, matched_keywords=matched_keywords)


def detect_danger(
    text: str, safety_keywords: list[str]
) -> tuple[DangerType, tuple[str, ...]]:
    """Classify explicit safety hazards using config-seeded vocabulary first."""

    normalized = normalize_text(text)
    configured_matches = [
        keyword for keyword in safety_keywords if normalize_text(keyword) in normalized
    ]

    if any(normalize_text(keyword) in normalized for keyword in _GAS_KEYWORDS):
        return DangerType.GAS_LEAK, tuple(configured_matches or ("gas",))
    if any(normalize_text(keyword) in normalized for keyword in _CO_KEYWORDS):
        return DangerType.CARBON_MONOXIDE, tuple(
            configured_matches or ("carbon monoxide",)
        )
    if any(normalize_text(keyword) in normalized for keyword in _ELECTRICAL_KEYWORDS):
        return DangerType.ELECTRICAL_HAZARD, tuple(configured_matches or ("smoke",))
    if any(normalize_text(keyword) in normalized for keyword in _FLOODING_KEYWORDS):
        return DangerType.FLOODING, tuple(configured_matches or ("flooding",))
    return DangerType.NONE, ()


def detect_issue_category(
    text: str,
    *,
    no_heat_keywords: list[str],
    no_cool_keywords: list[str],
) -> tuple[IssueCategory, tuple[str, ...]]:
    """Detect the primary HVAC issue category from the transcript."""

    no_heat_matches = find_keywords(text, tuple(no_heat_keywords))
    if no_heat_matches:
        return IssueCategory.NO_HEAT, no_heat_matches

    no_cool_matches = find_keywords(text, tuple(no_cool_keywords))
    if no_cool_matches:
        return IssueCategory.NO_COOL, no_cool_matches

    water_matches = find_keywords(text, _LEAKING_WATER_KEYWORDS)
    if water_matches:
        return IssueCategory.LEAKING_WATER, water_matches

    smell_matches = find_keywords(text, _BAD_SMELL_KEYWORDS)
    if smell_matches:
        return IssueCategory.BAD_SMELL, smell_matches

    return IssueCategory.OTHER, ()


def detect_urgency(
    text: str,
    *,
    danger_type: DangerType,
    issue_category: IssueCategory,
) -> UrgencyLevel:
    """Map safety + context cues to a stable urgency hint."""

    if danger_type != DangerType.NONE:
        return UrgencyLevel.EMERGENCY

    normalized = normalize_text(text)
    has_vulnerability = any(
        normalize_text(keyword) in normalized for keyword in _VULNERABILITY_KEYWORDS
    )
    has_urgent_situation = any(
        normalize_text(keyword) in normalized for keyword in _URGENT_SITUATION_KEYWORDS
    )

    if issue_category in {IssueCategory.NO_HEAT, IssueCategory.NO_COOL} and (
        has_vulnerability or has_urgent_situation
    ):
        return UrgencyLevel.URGENT

    if issue_category == IssueCategory.LEAKING_WATER:
        return UrgencyLevel.URGENT

    routine_matches = find_keywords(text, _ROUTINE_CALLBACK_KEYWORDS)
    if routine_matches:
        return UrgencyLevel.ROUTINE

    if issue_category != IssueCategory.OTHER:
        return UrgencyLevel.UNKNOWN

    return UrgencyLevel.UNKNOWN


def detect_address_relevance(
    text: str,
    *,
    danger_type: DangerType,
    issue_category: IssueCategory,
) -> bool:
    """Return whether asking for a service address is useful right now."""

    if danger_type != DangerType.NONE:
        return True
    if issue_category in {
        IssueCategory.NO_HEAT,
        IssueCategory.NO_COOL,
        IssueCategory.LEAKING_WATER,
        IssueCategory.BAD_SMELL,
    }:
        return True
    routine_matches = find_keywords(text, _ROUTINE_CALLBACK_KEYWORDS)
    if routine_matches:
        return False
    return issue_category != IssueCategory.OTHER
