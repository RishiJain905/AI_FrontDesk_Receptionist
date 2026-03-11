"""Business configuration data contract for HVAC intake agent."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BusinessConfig:
    """Runtime configuration passed to the conversational agent.

    List fields use ``default_factory=list`` so each config instance receives
    independent mutable containers.
    """

    business_name: str | None = None
    business_phone: str | None = None
    owner_phone: str | None = None
    timezone: str | None = None
    service_area: str | None = None
    emergency_instructions: str | None = None

    safety_keywords: list[str] = field(default_factory=list)
    no_heat_keywords: list[str] = field(default_factory=list)
    no_cool_keywords: list[str] = field(default_factory=list)
    dispatcher_contacts: list[str] = field(default_factory=list)
