"""Classification enums for HVAC agent intent and LLM output parsing.

These enums define the vocabulary used by the LLM classifier to categorize
customer issues, their urgency, and any immediate safety concerns. Each enum
subclasses `str` so values can be used directly as JSON-serializable strings
and compared with raw LLM output without conversion overhead.

Note: Python 3.11+ changed str(StrEnum) to return 'ClassName.MEMBER' instead
of the plain value. We override __str__ on each enum to restore the expected
behaviour (returning the raw value string) across all Python versions.
"""

from __future__ import annotations

from enum import Enum


class IssueCategory(str, Enum):
    """Primary category of the HVAC issue reported by the customer.

    Values are lowercase snake_case strings that match expected LLM output
    tokens and can be passed directly to downstream CRM or SMS systems.
    """

    def __str__(self) -> str:
        return self.value

    NO_HEAT = "no_heat"
    NO_COOL = "no_cool"
    POOR_AIRFLOW = "poor_airflow"
    STRANGE_NOISE = "strange_noise"
    BAD_SMELL = "bad_smell"
    LEAKING_WATER = "leaking_water"
    SYSTEM_SHORT_CYCLING = "system_short_cycling"
    THERMOSTAT_UNRESPONSIVE = "thermostat_unresponsive"
    OTHER = "other"


class UrgencyLevel(str, Enum):
    """Urgency classification for the reported HVAC issue.

    Used to determine dispatch priority and call-flow branching.
    ``EMERGENCY`` triggers an immediate safety protocol branch.
    ``UNKNOWN`` is the safe default when urgency cannot be determined.
    """

    def __str__(self) -> str:
        return self.value

    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"
    UNKNOWN = "unknown"


class DangerType(str, Enum):
    """Type of safety hazard associated with the reported issue, if any.

    ``NONE`` is the default when no hazard is indicated by the customer.
    Non-``NONE`` values trigger the emergency safety protocol regardless
    of the ``UrgencyLevel`` value.
    """

    def __str__(self) -> str:
        return self.value

    NONE = "none"
    GAS_LEAK = "gas_leak"
    CARBON_MONOXIDE = "carbon_monoxide"
    ELECTRICAL_HAZARD = "electrical_hazard"
    FLOODING = "flooding"
