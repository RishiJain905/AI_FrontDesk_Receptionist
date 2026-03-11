"""CRM service contracts and GoHighLevel provider exports."""

from services.crm.crm_service import CrmService
from services.crm.ghl_service import GoHighLevelService
from services.crm.mappers import (
    build_contact_note,
    build_contact_payload,
    to_ghl_contact,
    to_ghl_note,
)

__all__ = [
    "CrmService",
    "GoHighLevelService",
    "build_contact_note",
    "build_contact_payload",
    "to_ghl_contact",
    "to_ghl_note",
]
