"""Required-slot policy for adaptive HVAC intake."""

from __future__ import annotations

from enum import Enum

from hvac_types.classification import DangerType, IssueCategory

_NORMAL_REQUIRED_SLOTS = [
    "customer_name",
    "phone_number",
    "service_address",
    "issue_category",
]

_DANGER_MINIMUM_REQUIRED_SLOTS = [
    "customer_name",
    "phone_number",
    "issue_category",
]

_ADDRESS_OPTIONAL_ISSUES = {IssueCategory.OTHER}


class IntakeMode(str, Enum):
    """Requirement profiles for different intake risk levels."""

    NORMAL = "normal"
    DANGER_MINIMUM = "danger_minimum"

    def __str__(self) -> str:
        return self.value


def should_collect_address(
    *,
    address_relevant: bool | None = None,
    danger_type: DangerType = DangerType.NONE,
    issue_category: IssueCategory | None = None,
) -> bool:
    """Return whether service-address capture is currently worth asking for."""

    if danger_type != DangerType.NONE:
        return True
    if address_relevant is not None:
        return address_relevant
    if issue_category is None:
        return True
    return issue_category not in _ADDRESS_OPTIONAL_ISSUES


def get_required_slots(
    *,
    mode: IntakeMode,
    address_relevant: bool | None = None,
    danger_type: DangerType = DangerType.NONE,
    issue_category: IssueCategory | None = None,
) -> list[str]:
    """Return the required slot list in deterministic ask order."""

    if mode == IntakeMode.DANGER_MINIMUM:
        return list(_DANGER_MINIMUM_REQUIRED_SLOTS)

    required = list(_NORMAL_REQUIRED_SLOTS)
    if not should_collect_address(
        address_relevant=address_relevant,
        danger_type=danger_type,
        issue_category=issue_category,
    ):
        required.remove("service_address")
    return required
