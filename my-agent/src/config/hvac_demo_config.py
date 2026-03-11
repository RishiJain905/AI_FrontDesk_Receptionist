"""Default demo configuration profile for the HVAC after-hours voice agent."""

from __future__ import annotations

from hvac_types.business_config import BusinessConfig

HVAC_DEMO_CONFIG = BusinessConfig(
    business_name="North Star HVAC",
    business_phone="+1-416-555-0100",
    owner_phone="+1-416-555-0110",
    timezone="America/Toronto",
    service_area="Greater Toronto Area",
    emergency_instructions=(
        "If there is a gas smell, carbon monoxide alarm, smoke, sparks, or active flooding, "
        "tell the caller to leave the area immediately and call 911 before dispatching."
    ),
    safety_keywords=[
        "gas",
        "gas leak",
        "gas smell",
        "carbon monoxide",
        "co alarm",
        "smoke",
        "sparks",
        "electrical burning",
        "flooding",
    ],
    no_heat_keywords=[
        "no heat",
        "furnace not working",
        "heater not working",
        "cold house",
    ],
    no_cool_keywords=[
        "no cool",
        "ac not working",
        "air conditioner not cooling",
        "warm air",
    ],
    dispatcher_contacts=[
        "+1-416-555-0199",
        "+1-416-555-0110",
    ],
)
