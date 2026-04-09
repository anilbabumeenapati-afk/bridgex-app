print("🔥 NEW CODE RUNNING")

from typing import Optional, Dict, Any, List

from app.models.evidence_model import (
    EvidenceObject,
    FieldEvidence,
)
from app.config.versioning import (
    TAXONOMY_VERSION,
    MAPPING_VERSION,
    ENGINE_VERSION,
)
from app.core.validation.cross_field_engine import detect_cross_field_signals
from app.core.extraction.certifications import extract_certifications
from app.core.aggregation.conflict_resolver import resolve_certifications
from app.core.validation.validator import validate_all
from app.core.validation.gatekeeper import gatekeep_document
from app.core.analysis.risk_analyzer import (
    analyze_availability,
    analyze_incident,
)
from app.core.passport.passport_builder import build_passport
from app.core.aggregation.conflict_resolver import (
    resolve_availability,
    resolve_incident_time,
    resolve_data_residency,
)
from app.core.extraction.availability import extract_availability
from app.core.extraction.incident import extract_incident_time
from app.core.extraction.data_residency import extract_data_residency
from app.core.validation.drift_detector import detect_drift
from app.core.mapping.synonym_mapper import map_synonym
from app.db.repository import save_evidence, get_latest_version
from app.core.validation.claim_classifier import classify_field_claim
from app.core.validation.contradiction_detector import compare_claims


REQUIRED_FIELDS = [
    "operational_availability",
    "incident_notification_time",
    "data_residency",
    "security_certifications",
]


def classify_source_type(field_name: str) -> str:
    if field_name == "security_certifications":
        return "certification_document"
    if field_name in {"operational_availability", "incident_notification_time"}:
        return "vendor_document"
    if field_name == "data_residency":
        return "policy_or_hosting_statement"
    return "unknown"


def compute_binding_strength(field_dict: Dict[str, Any]) -> str:
    source = field_dict.get("source") or {}
    text = (source.get("text") or field_dict.get("source_text") or "").lower()

    weak_terms = [
        "may",
        "target",
        "aim",
        "typically",
        "generally",
        "designed to",
        "intended to",
        "in progress",
        "partial",
        "where possible",
    ]
    strong_terms = [
        "shall",
        "must",
        "guarantee",
        "guaranteed",
        "committed",
        "contractual",
        "sla",
    ]

    if any(term in text for term in strong_terms):
        return "strong"
    if any(term in text for term in weak_terms):
        return "weak"
    return "medium"


def compute_verification_tier(field_dict: Dict[str, Any]) -> str:
    trust = field_dict.get("trust") or {}
    source = field_dict.get("source") or {}

    source_type = trust.get("source_type") or "unknown"
    source_file = source.get("file") or "unknown"

    if source_type == "certification_document":
        return "document_backed"
    if source_file != "unknown":
        return "document_backed"
    return "self_attested"


def compute_trust_score(field_dict: Dict[str, Any]) -> int:
    score = 50

    lineage = field_dict.get("lineage") or {}
    risk = field_dict.get("risk") or {}
    validation = field_dict.get("validation") or {}
    trust = field_dict.get("trust") or {}

    confidence = lineage.get("confidence") or 0
    risk_flags = risk.get("flags") or []
    binding_strength = trust.get("binding_strength") or "medium"
    source_type = trust.get("source_type") or "unknown"
    value = field_dict.get("value")

    score += min(int(confidence * 20), 20)

    if binding_strength == "strong":
        score += 10
    elif binding_strength == "weak":
        score -= 10

    if source_type == "certification_document":
        score += 10
    elif source_type == "unknown":
        score -= 5

    if not value:
        score -= 25

    if risk_flags:
        score -= min(len(risk_flags) * 8, 24)

    validation_status = validation.get("status")
    if validation_status == "pass":
        score += 10
    elif validation_status == "fail":
        score -= 15

    return max(0, min(100, score))


def build_decision(field_dict: Dict[str, Any]) -> str:
    """
    Do not auto-approve based on extraction confidence.
    New extractions remain PENDING until reviewer action.
    """
    value = field_dict.get("value")
    if not value:
        return "PENDING"
    return "PENDING"


def build_field(field_name: str, raw: Dict[str, Any], extraction_rule: str) -> FieldEvidence:
    field = FieldEvidence(**raw)

    field.source.text = raw.get("source_text")
    field.source.page = raw.get("page")
    field.source.file = raw.get("source_file", "unknown")

    field.lineage.extraction_rule = extraction_rule
    field.lineage.confidence = raw.get("confidence", 0.9)
    field.lineage.mapped_field = raw.get("mapped_field")
    field.lineage.conflict = raw.get("conflict")

    field.trust.source_type = classify_source_type(field_name)

    return field


def finalize_field(
    field_name: str,
    field: FieldEvidence,
    validation_payload: Optional[Dict[str, Any]] = None,
) -> None:
    if validation_payload:
        field.validation = validation_payload

    field.risk.flags = field.risk.flags or []
    field.risk.trace = field.risk.trace or []

    field.trust.binding_strength = compute_binding_strength(field.dict())
    field.trust.verification_tier = compute_verification_tier(field.dict())
    field.trust.staleness_status = "unknown"
    field.trust.score = compute_trust_score(field.dict())

    field.review.decision = "REVIEW_REQUIRED"
    field.status = build_decision(field.dict())

    field.metadata["confidence"] = field.lineage.confidence
    field.metadata["priority"] = "high" if (field.trust.score or 0) < 60 else "medium"
    field.metadata["review_required"] = True


def build_state(evidence: EvidenceObject) -> None:
    evidence_fields = {
        "operational_availability": evidence.operational_availability,
        "incident_notification_time": evidence.incident_notification_time,
        "data_residency": evidence.data_residency,
        "security_certifications": evidence.security_certifications,
    }

    missing_fields: List[str] = []
    approved = 0
    total = len(evidence_fields)
    conflicts: List[Dict[str, Any]] = []

    for field_name, field in evidence_fields.items():
        if not field or not field.value:
            missing_fields.append(field_name)
            continue

        if field.status == "APPROVED":
            approved += 1

        if field.lineage and field.lineage.conflict:
            conflicts.append(
                {
                    "field": field_name,
                    "type": "resolver_conflict",
                    "details": field.lineage.conflict,
                }
            )

        if field.risk and field.risk.trace:
            for issue in field.risk.trace:
                if isinstance(issue, dict) and issue.get("conflict_type"):
                    conflicts.append(
                        {
                            "field": field_name,
                            "type": issue.get("conflict_type"),
                            "details": issue.get("details"),
                        }
                    )

    populated = total - len(missing_fields)
    completeness_percent = int((populated / total) * 100) if total else 0

    evidence.state.completeness_percent = completeness_percent
    evidence.state.missing_fields = missing_fields
    evidence.state.conflicts = conflicts
    evidence.state.review_progress = {
        "approved": approved,
        "total": total,
    }


def attach_claim_and_conflicts(
    field_name: str,
    field: FieldEvidence,
    previous_field: dict | None = None,
) -> None:
    claim = classify_field_claim(field_name, field.dict())
    field.metadata["claim"] = claim

    if claim.get("binding_strength"):
        field.trust.binding_strength = claim["binding_strength"]

    previous_claim = None
    if previous_field:
        previous_metadata = previous_field.get("metadata") or {}
        previous_claim = previous_metadata.get("claim")

    issues = compare_claims(
        field_name=field_name,
        current_field=field.dict(),
        current_claim=claim,
        previous_field=previous_field,
        previous_claim=previous_claim,
    )

    if issues:
        existing_flags = field.risk.flags or []
        existing_trace = field.risk.trace or []

        for issue in issues:
            conflict_type = issue.get("conflict_type")
            if conflict_type:
                existing_flags.append(conflict_type.upper())
            existing_trace.append(issue)

        field.risk.flags = list(dict.fromkeys(existing_flags))
        field.risk.trace = existing_trace


def load_previous_fields(record_id: int | None) -> dict:
    """
    Fetch latest saved evidence snapshot for this record_id, if available.
    Returns a dict keyed by field name, or {}.
    """
    if not record_id:
        return {}

    previous_version = get_latest_version(record_id)
    if not previous_version or not previous_version.evidence:
        return {}

    return previous_version.evidence


def extract_fields(pages, source_file: str = "unknown", record_id: int | None = None):
    print("A. extract_fields start")
    # =========================
    # 0. GATEKEEPING
    # =========================
    gate_result = gatekeep_document(pages)
    print("B. gatekeep done:", gate_result)

    if gate_result["status"] == "FAIL":
        return {
            "message": "Gatekeeping failed",
            "reason": gate_result["reason"],
        }

    if gate_result["status"] == "WARN":
        print("⚠ Gatekeeper warning:", gate_result["reason"])

    previous_evidence = load_previous_fields(record_id)
    print("C. previous evidence loaded")

    # =========================
    # 1. EXTRACTION
    # =========================
    availability_candidates = extract_availability(pages)
    print("D. availability extracted")
    incident_candidates = extract_incident_time(pages)
    print("D. availability extracted")
    data_residency_candidates = extract_data_residency(pages)
    print("E. incident extracted")

    availability_raw = resolve_availability(availability_candidates)
    print("F. residency extracted")
    incident_raw = resolve_incident_time(incident_candidates)
    print("G. availability resolved")
    data_residency_raw = resolve_data_residency(data_residency_candidates)
    print("H. incident resolved")

    cert_candidates = extract_certifications(pages)
    print("I. residency resolved")
    cert_raw = resolve_certifications(cert_candidates)
    print("J. certifications extracted")

    # =========================
    # 2. SYNONYM MAPPING
    # =========================
    if availability_raw:
        availability_raw["mapped_field"] = map_synonym(
            availability_raw.get("source_text")
        )
        availability_raw["source_file"] = availability_raw.get("source_file", source_file)

    if incident_raw:
        incident_raw["mapped_field"] = map_synonym(
            incident_raw.get("source_text")
        )
        incident_raw["source_file"] = incident_raw.get("source_file", source_file)

    if data_residency_raw:
        data_residency_raw["source_file"] = data_residency_raw.get("source_file", source_file)

    if cert_raw:
        cert_raw["source_file"] = cert_raw.get("source_file", source_file)

    # =========================
    # 3. BUILD FIELD OBJECTS
    # =========================
    availability = (
        build_field("operational_availability", availability_raw, "availability_regex_v1")
        if availability_raw
        else None
    )

    incident_time = (
        build_field("incident_notification_time", incident_raw, "incident_regex_v1")
        if incident_raw
        else None
    )

    data_residency = (
        build_field("data_residency", data_residency_raw, "data_residency_regex_v1")
        if data_residency_raw
        else None
    )

    certifications = (
        build_field("security_certifications", cert_raw, "certifications_regex_v1")
        if cert_raw
        else None
    )

    # =========================
    # 4. RISK METADATA
    # =========================
    if availability:
        analysis = analyze_availability(availability.dict())
        availability.risk.flags = analysis.get("risk_flags", [])
        availability.risk.trace = analysis.get("risk_trace", [])

    if incident_time:
        incident_analysis = analyze_incident(incident_time.dict())
        if isinstance(incident_analysis, dict):
            incident_time.risk.flags = incident_analysis.get("risk_flags", [])
            incident_time.risk.trace = incident_analysis.get("risk_trace", [])
        else:
            incident_time.risk.flags = incident_analysis or []

    # =========================
    # 5. VALIDATION INPUT
    # =========================
    evidence_dict = {
        "DORA_AVAILABILITY_METRIC": availability.dict() if availability else None,
        "DORA_INCIDENT_RESPONSE_TIME": incident_time.dict() if incident_time else None,
    }

    # =========================
    # 6. VALIDATION
    # =========================
    validation_result = validate_all(evidence_dict)

    if availability:
        finalize_field(
            "operational_availability",
            availability,
            validation_result["fields"].get("DORA_AVAILABILITY_METRIC"),
        )

    if incident_time:
        finalize_field(
            "incident_notification_time",
            incident_time,
            validation_result["fields"].get("DORA_INCIDENT_RESPONSE_TIME"),
        )

    if data_residency:
        finalize_field("data_residency", data_residency)

    if certifications:
        finalize_field("security_certifications", certifications)

    # =========================
    # 6.5 CLAIM CLASSIFICATION + CONTRADICTION DETECTION
    # =========================
    if availability:
        attach_claim_and_conflicts(
            "operational_availability",
            availability,
            previous_evidence.get("operational_availability"),
        )

    if incident_time:
        attach_claim_and_conflicts(
            "incident_notification_time",
            incident_time,
            previous_evidence.get("incident_notification_time"),
        )

    if data_residency:
        attach_claim_and_conflicts(
            "data_residency",
            data_residency,
            previous_evidence.get("data_residency"),
        )

    if certifications:
        attach_claim_and_conflicts(
            "security_certifications",
            certifications,
            previous_evidence.get("security_certifications"),
        )

    # =========================
    # 6.6 RECOMPUTE TRUST AFTER CONTRADICTIONS
    # =========================
    if availability:
        availability.trust.score = compute_trust_score(availability.dict())

    if incident_time:
        incident_time.trust.score = compute_trust_score(incident_time.dict())

    if data_residency:
        data_residency.trust.score = compute_trust_score(data_residency.dict())

    if certifications:
        certifications.trust.score = compute_trust_score(certifications.dict())

    # =========================
    # 7. FINAL OBJECT
    # =========================
    evidence = EvidenceObject(
        operational_availability=availability,
        incident_notification_time=incident_time,
        data_residency=data_residency,
        security_certifications=certifications,
    )

        # =========================
    # 6.7 CROSS-FIELD ENGINE
    # =========================
    cross_field_signals = detect_cross_field_signals(evidence.dict())

    build_state(evidence)
    
    if cross_field_signals:
        evidence.state.conflicts.extend(cross_field_signals)

    # =========================
    # 8. PASSPORT
    # =========================
    passport = {
        "operational_availability": build_passport(availability.dict()) if availability else None,
        "incident_notification_time": build_passport(incident_time.dict()) if incident_time else None,
        "data_residency": build_passport(data_residency.dict()) if data_residency else None,
        "security_certifications": build_passport(certifications.dict()) if certifications else None,
    }

    # =========================
    # 9. DRIFT
    # =========================
    drift_result = detect_drift(
        pages,
        {
            "operational_availability": availability,
            "incident_notification_time": incident_time,
        },
    )

    print("FINAL EVIDENCE:", evidence.dict())

    # =========================
    # 10. SAVE
    # =========================
    saved_record_id = save_evidence(
        evidence=evidence.dict(),
        validation=validation_result,
    )

    # =========================
    # 11. RESPONSE
    # =========================
    return {
        "record_id": saved_record_id,
        "message": f"Saved with ID {saved_record_id}",
        "evidence": evidence.dict(),
        "passport": passport,
        "validation": validation_result,
        "drift": drift_result,
        "meta": {
            "taxonomy_version": TAXONOMY_VERSION,
            "mapping_version": MAPPING_VERSION,
            "engine_version": ENGINE_VERSION,
            "missing_fields": evidence.state.missing_fields,
            "document_id": None,
            "source_hash": None,
            "source_file": source_file,
        },
    }