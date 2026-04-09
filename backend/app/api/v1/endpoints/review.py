from datetime import datetime
from fastapi import APIRouter

from app.db.repository import get_record, update_record, log_audit, save_version
from app.core.mapping.dpm_mapper import map_to_dpm
from app.core.reporting.report_generator import generate_json_report
from app.core.reporting.zip_generator import create_zip
from app.core.validation.exception_engine import build_exceptions
from app.core.validation.validator import validate_all
from app.core.enrichment.metadata_enricher import enrich_evidence
from app.core.validation.conflict_summarizer import summarize_conflicts

router = APIRouter()

RELEVANT_FIELDS = [
    "operational_availability",
    "incident_notification_time",
    "data_residency",
    "security_certifications",
]


def _field_has_extracted_evidence(field: dict | None) -> bool:
    if not isinstance(field, dict):
        return False

    normalized = field.get("normalized") or {}
    source = field.get("source") or {}
    lineage = field.get("lineage") or {}

    has_normalized = (
        isinstance(normalized, dict)
        and (
            normalized.get("min") is not None
            or normalized.get("max") is not None
        )
    )

    has_source = bool(
        source.get("text")
        or source.get("raw_text")
        or lineage.get("source_text")
        or lineage.get("raw_text")
        or field.get("source_text")
    )

    has_value = field.get("value") is not None

    return has_normalized or has_source or has_value


def all_fields_approved(evidence: dict) -> bool:
    """
    Pilot-friendly rule:
    only fields that actually have extracted evidence must be approved.
    Missing/unextracted fields do not block finalization.
    """
    extracted_fields = []

    for field_name in RELEVANT_FIELDS:
        field = evidence.get(field_name)
        if _field_has_extracted_evidence(field):
            extracted_fields.append(field_name)

    if not extracted_fields:
        return False

    return all(
        isinstance(evidence.get(field_name), dict)
        and evidence[field_name].get("status") == "APPROVED"
        for field_name in extracted_fields
    )


def recompute_state(evidence: dict) -> dict:
    missing_fields = []
    approved = 0
    conflicts = []

    for field_name in RELEVANT_FIELDS:
        field = evidence.get(field_name)

        if not _field_has_extracted_evidence(field):
            missing_fields.append(field_name)
            continue

        if field.get("status") == "APPROVED":
            approved += 1

        lineage = field.get("lineage") or {}
        if lineage.get("conflict"):
            conflicts.append({
                "field": field_name,
                "type": "resolver_conflict",
                "details": lineage.get("conflict"),
            })

        risk = field.get("risk") or {}
        trace = risk.get("trace") or []
        for issue in trace:
            if isinstance(issue, dict) and issue.get("conflict_type"):
                conflicts.append({
                    "field": field_name,
                    "type": issue.get("conflict_type"),
                    "details": issue.get("details"),
                })

    total = len(RELEVANT_FIELDS)
    populated = total - len(missing_fields)
    completeness_percent = int((populated / total) * 100) if total else 0

    evidence["state"] = {
        "completeness_percent": completeness_percent,
        "missing_fields": missing_fields,
        "conflicts": conflicts,
        "conflict_summaries": summarize_conflicts(conflicts),
        "review_progress": {
            "approved": approved,
            "total": total,
        },
    }

    return evidence


def normalize_for_ui(evidence: dict):
    for field_name, field in evidence.items():
        if not isinstance(field, dict):
            continue

        if field_name in {"state", "vendor_profile"}:
            continue

        normalized = field.get("normalized")
        value = field.get("value")

        if isinstance(normalized, dict):
            field["normalized"] = {
                "min": normalized.get("min"),
                "max": normalized.get("max"),
                "unit": normalized.get("unit"),
            }
        elif isinstance(normalized, (int, float)):
            field["normalized"] = {
                "min": normalized,
                "max": normalized,
                "unit": None,
            }
        elif isinstance(value, (int, float)):
            field["normalized"] = {
                "min": value,
                "max": value,
                "unit": None,
            }
        elif isinstance(value, dict):
            field["normalized"] = {
                "min": value.get("min"),
                "max": value.get("max"),
                "unit": value.get("unit"),
            }
        else:
            field["normalized"] = {
                "min": None,
                "max": None,
                "unit": None,
            }

        field["metadata"] = field.get("metadata") or {}

        confidence = (
            field.get("confidence")
            or field["metadata"].get("confidence")
            or (field.get("lineage") or {}).get("confidence")
        )
        field["metadata"]["confidence"] = confidence

        source = field.get("source") or {}
        lineage = field.get("lineage") or {}

        raw_text = (
            source.get("text")
            or source.get("raw_text")
            or lineage.get("raw_text")
            or lineage.get("source_text")
            or field.get("source_text")
        )
        page = source.get("page") or lineage.get("page") or field.get("page")
        source_file = source.get("file") or lineage.get("source_file")
        extraction_rule = source.get("rule") or lineage.get("extraction_rule")

        field["source"] = {
            "text": raw_text,
            "raw_text": raw_text,
            "page": page,
            "file": source_file,
            "rule": extraction_rule,
        }

        field["lineage"] = {
            "source_text": raw_text,
            "raw_text": raw_text,
            "page": page,
            "file": source_file,
            "source_file": source_file,
            "confidence": lineage.get("confidence"),
            "extraction_rule": extraction_rule,
            "mapped_field": lineage.get("mapped_field"),
            "conflict": lineage.get("conflict"),
        }

        risk = field.get("risk") or {}
        risk_flags = risk.get("flags", field.get("risk_flags", []))
        field["risk"] = {
            "flags": risk_flags,
            "trace": risk.get("trace", []),
            "severity": risk.get("severity"),
        }
        field["risk_flags"] = risk_flags

        trust = field.get("trust") or {}
        field["trust"] = {
            "score": trust.get("score"),
            "verification_tier": trust.get("verification_tier"),
            "binding_strength": trust.get("binding_strength"),
            "source_type": trust.get("source_type"),
            "staleness_status": trust.get("staleness_status"),
        }

        review = field.get("review") or {}
        field["review"] = {
            "decision": review.get("decision"),
            "reviewer": review.get("reviewer"),
            "timestamp": review.get("timestamp"),
            "reason": review.get("reason"),
        }

    return recompute_state(evidence)


def format_exception(issue, fallback_field):
    field = issue.get("field", fallback_field)
    issue_type = issue.get("issue")
    details = issue.get("details", "")

    if issue_type == "non_binding_language":
        return {
            "field": field,
            "message": f"⚠ Weak or non-binding language detected ({details})",
            "action": "Use strict terms like 'shall' or 'must'",
            "severity": "medium",
        }

    elif issue_type == "missing_value":
        return {
            "field": field,
            "message": "Required value is missing",
            "action": "Provide a valid value",
            "severity": "high",
        }

    elif issue_type == "threshold_breach":
        return {
            "field": field,
            "message": f"Value outside allowed threshold ({details})",
            "action": "Adjust to meet regulatory limits",
            "severity": "high",
        }

    elif issue_type == "range_conflict":
        return {
            "field": field,
            "message": f"Range conflict detected ({details})",
            "action": "Review normalized values",
            "severity": "high",
        }

    return {
        "field": field,
        "message": details or issue_type or "Unknown issue",
        "action": "Review field manually",
        "severity": "low",
    }


def _update_review_block(field: dict, decision: str, reason: str):
    review = field.get("review") or {}
    review["decision"] = decision
    review["timestamp"] = datetime.utcnow().isoformat()
    review["reason"] = reason
    field["review"] = review


@router.post("/approve/{record_id}/{field_name}")
def approve_field(record_id: int, field_name: str):
    record = get_record(record_id)

    if not record:
        return {"error": "Record not found"}

    evidence = record.evidence or {}

    if field_name not in evidence:
        return {"error": "Field not found"}

    field_obj = evidence.get(field_name)

    if not isinstance(field_obj, dict):
        return {"error": f"Field '{field_name}' has no extracted evidence to approve"}

    old_value = field_obj.copy()

    evidence[field_name]["status"] = "APPROVED"
    _update_review_block(
        evidence[field_name],
        decision="APPROVED",
        reason="Manual approval by reviewer",
    )

    log_audit(
        record_id=record_id,
        field_name=field_name,
        action="APPROVED",
        old_value=old_value,
        new_value=evidence[field_name],
    )

    update_record(record_id, evidence)

    version = save_version(
        record_id=record_id,
        evidence=evidence,
        validation=record.validation,
    )

    evidence = enrich_evidence(evidence)
    evidence = normalize_for_ui(evidence)

    if not all_fields_approved(evidence):
        return {
            "message": f"{field_name} approved. Waiting for other extracted fields.",
            "version": version,
            "evidence": evidence,
        }

    raw_exceptions = build_exceptions(evidence)
    exceptions = []

    if isinstance(raw_exceptions, dict):
        for field, issues in raw_exceptions.items():
            for issue in issues:
                if isinstance(issue, dict):
                    exceptions.append(format_exception(issue, field))

    elif isinstance(raw_exceptions, list):
        for issue in raw_exceptions:
            if isinstance(issue, dict):
                exceptions.append(format_exception(issue, "unknown"))

    validation_input = {
        fname: field_data
        for fname, field_data in evidence.items()
        if isinstance(field_data, dict) and fname not in {"vendor_profile", "state"}
    }

    validation_result = validate_all(validation_input)

    dpm_output = map_to_dpm(evidence)
    report = generate_json_report(dpm_output)

    csv_file = report["csv"].replace("output/", "")
    metadata_file = report["metadata"].replace("output/", "")

    create_zip(
        report["csv"],
        report["metadata"],
        "output/report_bundle.zip",
    )

    return {
        "message": "Approved extracted fields. XBRL-CSV generated.",
        "version": version,
        "evidence": evidence,
        "validation": validation_result,
        "exceptions": exceptions,
        "dpm_mapping": dpm_output,
        "xbrl_csv": {
            "csv": csv_file,
            "metadata": metadata_file,
        },
        "zip": "report_bundle.zip",
    }


@router.post("/reject/{record_id}/{field_name}")
def reject_field(record_id: int, field_name: str):
    record = get_record(record_id)

    if not record:
        return {"error": "Record not found"}

    evidence = record.evidence or {}

    if field_name not in evidence:
        return {"error": "Field not found"}

    field_obj = evidence.get(field_name)

    if not isinstance(field_obj, dict):
        return {"error": f"Field '{field_name}' has no extracted evidence to reject"}

    old_value = field_obj.copy()

    evidence[field_name]["status"] = "REJECTED"
    _update_review_block(
        evidence[field_name],
        decision="REJECTED",
        reason="Manual rejection by reviewer",
    )

    log_audit(
        record_id=record_id,
        field_name=field_name,
        action="REJECTED",
        old_value=old_value,
        new_value=evidence[field_name],
    )

    update_record(record_id, evidence)

    version = save_version(
        record_id=record_id,
        evidence=evidence,
        validation=record.validation,
    )

    evidence = enrich_evidence(evidence)
    evidence = normalize_for_ui(evidence)

    return {
        "message": f"{field_name} rejected.",
        "version": version,
        "evidence": evidence,
    }