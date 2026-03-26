from app.models.evidence import (
    EvidenceObject,
    FieldEvidence
)
from app.config.versioning import (
    TAXONOMY_VERSION,
    MAPPING_VERSION,
    ENGINE_VERSION
)

from app.core.validation.validator import validate_all
from app.core.validation.gatekeeper import gatekeep_document
from app.core.analysis.risk_analyzer import (
    analyze_availability,
    analyze_incident
)
from app.core.passport.passport_builder import build_passport

from app.core.aggregation.conflict_resolver import (
    resolve_availability,
    resolve_incident_time
)

from app.core.extraction.availability import extract_availability
from app.core.extraction.incident import extract_incident_time
from app.core.validation.drift_detector import detect_drift

from app.core.mapping.synonym_mapper import map_synonym

from app.db.repository import save_evidence


# -------------------------
# DECISION LOGIC
# -------------------------
def assign_decision(field: dict):
    confidence = field.get("lineage", {}).get("confidence", 0)

    if confidence >= 0.9:
        return "APPROVED"
    else:
        return "PENDING"


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

    availability_raw = resolve_availability(availability_candidates)
    incident_raw = resolve_incident_time(incident_candidates)

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

    # =========================
    # 5. RISK METADATA (FIXED)
    # =========================
    if availability:
        analysis = analyze_availability(availability.dict())

        print("AVAILABILITY ANALYSIS:", analysis)

        availability.lineage["risk_flags"] = analysis.get("risk_flags", [])
        availability.lineage["risk_trace"] = analysis.get("risk_trace", [])

    if incident_time:
        incident_analysis = analyze_incident(incident_time.dict())

        print("INCIDENT ANALYSIS:", incident_analysis)

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
        incident_notification_time=incident_time
    )

    # =========================
    # 10. PASSPORT
    # =========================
    passport = {
        "operational_availability": build_passport(availability.dict()) if availability else None,
        "incident_notification_time": build_passport(incident_time.dict()) if incident_time else None
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
            "engine_version": ENGINE_VERSION
        }
    }