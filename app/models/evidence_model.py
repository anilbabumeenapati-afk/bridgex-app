from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal


class FieldEvidence(BaseModel):
    value: Optional[str] = None
    source_text: Optional[str] = None
    page: Optional[int] = None

    normalized: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    lineage: Optional[Dict[str, Any]] = None

    status: Literal["PENDING", "APPROVED", "REJECTED", "MODIFIED"] = "PENDING"


class EvidenceObject(BaseModel):
    operational_availability: Optional[FieldEvidence] = None
    incident_notification_time: Optional[FieldEvidence] = None
    data_residency: Optional[FieldEvidence] = None
    security_certifications: Optional[FieldEvidence] = None