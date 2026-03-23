from fastapi import APIRouter
from app.db.repository import get_record, update_record, log_audit, save_version
from app.db.session import SessionLocal
from app.db.models import AuditLog, EvidenceVersion

from app.core.mapping.dpm_mapper import map_to_dpm
from app.core.reporting.report_generator import generate_json_report
from app.core.reporting.zip_generator import create_zip
from app.core.validation.exception_engine import build_exceptions
from app.core.validation.validator import validate_all

router = APIRouter()


# -------------------------
# CHECK: all fields approved
# -------------------------
def all_fields_approved(evidence: dict):
    return all(
        field and field.get("status") == "APPROVED"
        for field in evidence.values()
    )


# -------------------------
# NORMALIZATION
# -------------------------
def normalize_for_ui(evidence: dict):
    for field_name, field in evidence.items():
        if not field:
            continue

        normalized = field.get("normalized")
        value = field.get("value")

        # Ensure normalized always has {min, max}
        if isinstance(normalized, dict):
            field["normalized"] = {
                "min": normalized.get("min"),
                "max": normalized.get("max")
            }

        elif isinstance(normalized, (int, float)):
            field["normalized"] = {"min": normalized, "max": normalized}

        elif isinstance(value, (int, float)):
            field["normalized"] = {"min": value, "max": value}

        elif isinstance(value, dict):
            field["normalized"] = {
                "min": value.get("min"),
                "max": value.get("max")
            }

        else:
            field["normalized"] = {"min": None, "max": None}

        # metadata
        field["metadata"] = field.get("metadata", {})

        confidence = (
            field.get("confidence")
            or field["metadata"].get("confidence")
            or field.get("lineage", {}).get("confidence")
        )

        field["metadata"]["confidence"] = confidence

        field["metadata"]["priority"] = (
            "high" if confidence is not None and confidence < 0.8 else "medium"
        )

        field["metadata"]["review_required"] = (
            (confidence is not None and confidence < 0.85)
            or len(field.get("risk_flags", [])) > 0
        )

        lineage = field.get("lineage", {})

        field["lineage"] = {
            "source_text": lineage.get("source_text") or field.get("source_text"),
            "page": lineage.get("page") or field.get("page")
        }

    return evidence


# -------------------------
# 🔥 UPGRADED EXCEPTION FORMATTER
# -------------------------
def format_exception(issue, fallback_field):
    field = issue.get("field", fallback_field)
    issue_type = issue.get("issue")
    details = issue.get("details", "")

    if issue_type == "non_binding_language":
        return {
            "field": field,
            "message": f"⚠ Weak or non-binding language detected ({details})",
            "action": "Use strict terms like 'shall' or 'must'",
            "severity": "medium"
        }

    elif issue_type == "missing_value":
        return {
            "field": field,
            "message": "Required value is missing",
            "action": "Provide a valid value",
            "severity": "high"
        }

    elif issue_type == "threshold_breach":
        return {
            "field": field,
            "message": f"Value outside allowed threshold ({details})",
            "action": "Adjust to meet regulatory limits",
            "severity": "high"
        }

    return {
        "field": field,
        "message": details or issue_type or "Unknown issue",
        "action": "Review field manually",
        "severity": "low"
    }


# -------------------------
# APPROVE FIELD
# -------------------------
@router.post("/approve/{record_id}/{field_name}")
def approve_field(record_id: int, field_name: str):
    record = get_record(record_id)

    if not record:
        return {"error": "Record not found"}

    evidence = record.evidence

    if field_name not in evidence:
        return {"error": "Field not found"}

    old_value = evidence[field_name].copy()

    evidence[field_name]["status"] = "APPROVED"

    log_audit(
        record_id=record_id,
        field_name=field_name,
        action="APPROVED",
        old_value=old_value,
        new_value=evidence[field_name]
    )

    update_record(record_id, evidence)

    version = save_version(
        record_id=record_id,
        evidence=evidence,
        validation=record.validation
    )

    # -------------------------
    # NOT COMPLETE
    # -------------------------
    if not all_fields_approved(evidence):
        evidence = normalize_for_ui(evidence)
        return {
            "message": f"{field_name} approved. Waiting for other fields.",
            "version": version,
            "evidence": evidence
        }

    # -------------------------
    # ALL APPROVED
    # -------------------------
    evidence = normalize_for_ui(evidence)

    # -------------------------
    # EXCEPTIONS (UPGRADED)
    # -------------------------
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

    # -------------------------
    # VALIDATION
    # -------------------------
    validation_input = {
        fname: field_data for fname, field_data in evidence.items()
    }

    validation_result = validate_all(validation_input)

    # -------------------------
    # REPORT
    # -------------------------
    dpm_output = map_to_dpm(evidence)
    report = generate_json_report(dpm_output)

    csv_file = report["csv"].replace("output/", "")
    metadata_file = report["metadata"].replace("output/", "")

    zip_path = create_zip(
        report["csv"],
        report["metadata"],
        "output/report_bundle.zip"
    )

    return {
        "message": "All fields approved. XBRL-CSV generated.",
        "version": version,
        "evidence": evidence,
        "validation": validation_result,
        "exceptions": exceptions,
        "dpm_mapping": dpm_output,
        "xbrl_csv": {
            "csv": csv_file,
            "metadata": metadata_file
        },
        "zip": "report_bundle.zip"
    }


# -------------------------
# REJECT FIELD
# -------------------------
@router.post("/reject/{record_id}/{field_name}")
def reject_field(record_id: int, field_name: str):
    record = get_record(record_id)

    if not record:
        return {"error": "Record not found"}

    evidence = record.evidence

    if field_name not in evidence:
        return {"error": "Field not found"}

    old_value = evidence[field_name].copy()

    evidence[field_name]["status"] = "REJECTED"

    log_audit(
        record_id=record_id,
        field_name=field_name,
        action="REJECTED",
        old_value=old_value,
        new_value=evidence[field_name]
    )

    update_record(record_id, evidence)

    version = save_version(
        record_id=record_id,
        evidence=evidence,
        validation=record.validation
    )

    evidence = normalize_for_ui(evidence)

    return {
        "message": f"{field_name} rejected",
        "version": version,
        "evidence": evidence
    }


# -------------------------
# AUDIT LOGS
# -------------------------
@router.get("/audit/{record_id}")
def get_audit_logs(record_id: int):
    db = SessionLocal()
    logs = db.query(AuditLog).filter(
        AuditLog.record_id == record_id
    ).all()
    db.close()
    return logs


# -------------------------
# VERSIONS
# -------------------------
@router.get("/versions/{record_id}")
def get_versions(record_id: int):
    db = SessionLocal()
    versions = db.query(EvidenceVersion).filter(
        EvidenceVersion.record_id == record_id
    ).all()
    db.close()
    return versions