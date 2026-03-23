from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal


# 🔹 Individual field (availability, incident time, etc.)
class FieldEvidence(BaseModel):
    value: Optional[str] = None

    # 🔥 KEEP original raw context
    source_text: Optional[str] = None
    page: Optional[int] = None

    # 🔹 structured normalized data
    normalized: Optional[Dict[str, Any]] = None

    # 🔹 validation result
    validation: Optional[Dict[str, Any]] = None

    # 🔥 CRITICAL: lineage for traceability
    lineage: Optional[Dict[str, Any]] = None

    # 🔹 review status
    status: Literal["PENDING", "APPROVED", "REJECTED", "MODIFIED"] = "PENDING"


# 🔹 Full evidence object (canonical structure)
class EvidenceObject(BaseModel):
    operational_availability: Optional[FieldEvidence] = None
    incident_notification_time: Optional[FieldEvidence] = None


# 🔹 Validation summary
class ValidationSummary(BaseModel):
    availability: Optional[Dict[str, Any]] = None
    incident_time: Optional[Dict[str, Any]] = None


# 🔹 Final API response
class ExtractionResponse(BaseModel):
    record_id: Optional[int] = None
    evidence: EvidenceObject
    validation: Optional[ValidationSummary] = None
    dpm_mapping: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    message: Optional[str] = None