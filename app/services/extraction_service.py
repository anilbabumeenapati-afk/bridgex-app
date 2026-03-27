print("🔥 NEW CODE RUNNING")
from app.models.evidence_model import (
    EvidenceObject,
    FieldEvidence
)
from app.config.versioning import (
    TAXONOMY_VERSION,
    MAPPING_VERSION,
    ENGINE_VERSION
)
from app.core.extraction.certifications import extract_certifications
from app.core.aggregation.conflict_resolver import resolve_certifications
from app.core.validation.validator import validate_all
from app.core.validation.gatekeeper import gatekeep_document
from app.core.analysis.risk_analyzer import (
    analyze_availability,
    analyze_incident
)
from app.core.passport.passport_builder import build_passport

from app.core.aggregation.conflict_resolver import (
    resolve_availability,
    resolve_incident_time,
    resolve_data_residency
)

from app.core.extraction.availability import extract_availability
from app.core.extraction.incident import extract_incident_time
from app.core.extraction.data_residency import extract_data_residency

from app.core.validation.drift_detector import detect_drift
from app.core.mapping.synonym_mapper import map_synonym
from app.db.repository import save_evidence


# -------------------------
# DECISION LOGIC
# -------------------------
def assign_decision(field: dict):
    confidence = field.get("lineage", {}).get("confidence", 0)
    return "APPROVED" if confidence >= 0.9 else "PENDING"


# -------------------------
# MAIN EXTRACTION FUNCTION
# -------------------------
def extract_fields(pages):

    # =========================
    # 0. GATEKEEPING
    # =========================
    gate_result = gatekeep_document(pages)

    if gate_result["status"] == "FAIL":
        return {
            "message": "Gatekeeping failed",
            "reason": gate_result["reason"]
        }

    if gate_result["status"] == "WARN":
        print("⚠ Gatekeeper warning:", gate_result["reason"])

    # =========================
    # 1. EXTRACTION
    # =========================
    availability_candidates = extract_availability(pages)
    incident_candidates = extract_incident_time(pages)
    data_residency_candidates = extract_data_residency(pages)

    availability_raw = resolve_availability(availability_candidates)
    incident_raw = resolve_incident_time(incident_candidates)
    data_residency_raw = resolve_data_residency(data_residency_candidates)
    cert_candidates = extract_certifications(pages)
    cert_raw = resolve_certifications(cert_candidates)

    # =========================
    # 2. SYNONYM MAPPING
    # =========================
    if availability_raw:
        availability_raw["mapped_field"] = map_synonym(
            availability_raw.get("source_text")
        )

    if incident_raw:
        incident_raw["mapped_field"] = map_synonym(
            incident_raw.get("source_text")
        )

    # =========================
    # 3. BUILD FIELD OBJECTS
    # =========================
    availability = FieldEvidence(**availability_raw) if availability_raw else None
    incident_time = FieldEvidence(**incident_raw) if incident_raw else None
    data_residency = FieldEvidence(**data_residency_raw) if data_residency_raw else FieldEvidence()
    certifications = FieldEvidence(**cert_raw) if cert_raw else FieldEvidence()

    # =========================
    # 4. ATTACH LINEAGE
    # =========================
    if availability:
        availability.lineage = {
            "raw_text": availability_raw.get("source_text"),
            "page": availability_raw.get("page"),
            "extraction_rule": "availability_regex_v1",
            "confidence": availability_raw.get("confidence", 0.9),
            "source_file": availability_raw.get("source_file", "unknown"),
            "conflict": availability_raw.get("conflict"),
            "mapped_field": availability_raw.get("mapped_field")
        }

    if incident_time:
        incident_time.lineage = {
            "raw_text": incident_raw.get("source_text"),
            "page": incident_raw.get("page"),
            "extraction_rule": "incident_regex_v1",
            "confidence": incident_raw.get("confidence", 0.9),
            "source_file": incident_raw.get("source_file", "unknown"),
            "conflict": incident_raw.get("conflict"),
            "mapped_field": incident_raw.get("mapped_field")
        }

    if data_residency and data_residency_raw:
        data_residency.lineage = {
            "raw_text": data_residency_raw.get("source_text"),
            "page": data_residency_raw.get("page"),
            "extraction_rule": "data_residency_regex_v1",
            "confidence": data_residency_raw.get("confidence", 0.9),
            "source_file": data_residency_raw.get("source_file", "unknown"),
            "conflict": data_residency_raw.get("conflict")
        }
    
    if certifications and cert_raw:
        certifications.lineage = {
            "raw_text": cert_raw.get("source_text"),
            "page": cert_raw.get("page"),
            "extraction_rule": "certifications_regex_v1",
            "confidence": cert_raw.get("confidence", 0.95),
            "source_file": cert_raw.get("source_file", "unknown"),
            "conflict": cert_raw.get("conflict")
    }

    # =========================
    # 5. RISK METADATA
    # =========================
    if availability:
        analysis = analyze_availability(availability.dict())
        availability.lineage["risk_flags"] = analysis.get("risk_flags", [])
        availability.lineage["risk_trace"] = analysis.get("risk_trace", [])

    if incident_time:
        incident_analysis = analyze_incident(incident_time.dict())
        incident_time.lineage["risk_flags"] = incident_analysis or []

    # =========================
    # 6. AUTO DECISION
    # =========================
    if availability:
        availability.status = assign_decision(availability.dict())
        availability.lineage["decision"] = {
            "type": "AUTO_APPROVED" if availability.status == "APPROVED" else "REVIEW",
            "threshold": 0.9
        }

    if incident_time:
        incident_time.status = assign_decision(incident_time.dict())
        incident_time.lineage["decision"] = {
            "type": "AUTO_APPROVED" if incident_time.status == "APPROVED" else "REVIEW",
            "threshold": 0.9
        }

    # =========================
    # 7. VALIDATION INPUT
    # =========================
    evidence_dict = {
        "DORA_AVAILABILITY_METRIC": availability.dict() if availability else None,
        "DORA_INCIDENT_RESPONSE_TIME": incident_time.dict() if incident_time else None
    }

    # =========================
    # 8. VALIDATION
    # =========================
    validation_result = validate_all(evidence_dict)

    if availability:
        availability.validation = validation_result["fields"].get("DORA_AVAILABILITY_METRIC")

    if incident_time:
        incident_time.validation = validation_result["fields"].get("DORA_INCIDENT_RESPONSE_TIME")

    # =========================
    # 9. FINAL OBJECT
    # =========================
    evidence = EvidenceObject(
        operational_availability=availability,
        incident_notification_time=incident_time,
        data_residency=data_residency,
        security_certifications=certifications
    )

    # =========================
    # 10. PASSPORT
    # =========================
    passport = {
        "operational_availability": build_passport(availability.dict()) if availability else None,
        "incident_notification_time": build_passport(incident_time.dict()) if incident_time else None,
        "data_residency": build_passport(data_residency.dict()) if data_residency else None,
        "security_certifications": build_passport(certifications.dict()) if certifications else None
    }

    # =========================
    # 11. DRIFT
    # =========================
    drift_result = detect_drift(
        pages,
        {
            "operational_availability": availability,
            "incident_notification_time": incident_time
        }
    )

    print("FINAL EVIDENCE:", evidence.dict())

    # =========================
    # 12. SAVE
    # =========================
    record_id = save_evidence(
        evidence=evidence.dict(),
        validation=validation_result
    )

    # =========================
# 12.5 MISSING FIELDS
# =========================
    missing_fields = []

    if not availability or not availability.value:
        missing_fields.append("operational_availability")

    if not incident_time or not incident_time.value:
        missing_fields.append("incident_notification_time")

    if not data_residency or not data_residency.value:
        missing_fields.append("data_residency")

    if not certifications or not certifications.value:
        missing_fields.append("security_certifications")
    # =========================
    # 13. RESPONSE
    # =========================
    return {
        "record_id": record_id,
        "message": f"Saved with ID {record_id}",
        "evidence": evidence.dict(),
        "passport": passport,
        "validation": validation_result,
        "drift": drift_result,
        "meta": {
            "taxonomy_version": TAXONOMY_VERSION,
            "mapping_version": MAPPING_VERSION,
            "engine_version": ENGINE_VERSION,
            "missing_fields": missing_fields,
            "document_id": "doc_001",   # 🔥 ADD
            "source_hash": "abc123" 
        }
    }