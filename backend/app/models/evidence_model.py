from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal


class FieldSource(BaseModel):
    text: Optional[str] = None
    page: Optional[int] = None
    file: Optional[str] = None


class FieldLineage(BaseModel):
    extraction_rule: Optional[str] = None
    confidence: Optional[float] = None
    mapped_field: Optional[str] = None
    conflict: Optional[Any] = None
    source_hash: Optional[str] = None
    document_id: Optional[str] = None


class FieldRisk(BaseModel):
    flags: List[str] = Field(default_factory=list)
    trace: List[Any] = Field(default_factory=list)
    severity: Optional[str] = None


class FieldTrust(BaseModel):
    score: Optional[int] = None
    verification_tier: Optional[str] = None
    binding_strength: Optional[str] = None
    source_type: Optional[str] = None
    staleness_status: Optional[str] = None


class FieldReview(BaseModel):
    decision: Optional[str] = None
    reviewer: Optional[str] = None
    timestamp: Optional[str] = None
    reason: Optional[str] = None


class FieldEvidence(BaseModel):
    value: Optional[Any] = None
    source_text: Optional[str] = None
    page: Optional[int] = None

    normalized: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None

    source: FieldSource = Field(default_factory=FieldSource)
    lineage: FieldLineage = Field(default_factory=FieldLineage)
    risk: FieldRisk = Field(default_factory=FieldRisk)
    trust: FieldTrust = Field(default_factory=FieldTrust)
    review: FieldReview = Field(default_factory=FieldReview)

    metadata: Dict[str, Any] = Field(default_factory=dict)

    status: Literal["PENDING", "APPROVED", "REJECTED", "MODIFIED"] = "PENDING"


class VendorProfile(BaseModel):
    vendor_name: Optional[str] = None
    service_type: Optional[str] = None
    criticality: Optional[str] = None
    risk_level: Optional[str] = None
    dependency: Optional[str] = None
    contract_status: Optional[str] = None


class StatePanel(BaseModel):
    completeness_percent: int = 0
    missing_fields: List[str] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    review_progress: Dict[str, int] = Field(default_factory=lambda: {"approved": 0, "total": 0})


class EvidenceObject(BaseModel):
    vendor_profile: VendorProfile = Field(default_factory=VendorProfile)

    operational_availability: Optional[FieldEvidence] = None
    incident_notification_time: Optional[FieldEvidence] = None
    data_residency: Optional[FieldEvidence] = None
    security_certifications: Optional[FieldEvidence] = None

    state: StatePanel = Field(default_factory=StatePanel)