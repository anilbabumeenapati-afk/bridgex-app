from typing import Any, Dict, Optional


def _safe_text(field: Dict[str, Any]) -> str:
    source = field.get("source") or {}
    lineage = field.get("lineage") or {}

    text = (
        source.get("text")
        or lineage.get("raw_text")
        or lineage.get("source_text")
        or field.get("source_text")
        or ""
    )

    return str(text).strip().lower()


def classify_binding_strength(text: str) -> str:
    strong_terms = [
        "shall",
        "must",
        "guarantee",
        "guaranteed",
        "committed",
        "contractual",
        "sla",
        "within",
        "not exceed",
    ]

    weak_terms = [
        "may",
        "might",
        "target",
        "expected",
        "indicative",
        "approximately",
        "approx",
        "usually",
        "realistically",
        "subject to",
        "where possible",
        "in progress",
        "partial",
        "designed to",
        "intended to",
    ]

    if any(term in text for term in strong_terms):
        return "strong"

    if any(term in text for term in weak_terms):
        return "weak"

    return "medium"


def classify_metric_kind(field_name: str, text: str) -> str:
    """
    Returns a coarse semantic type for the extracted claim.
    """

    if field_name == "operational_availability":
        if "sla" in text or "contractual" in text:
            return "sla_commitment"
        if "historically" in text or "rolling 12-month" in text or "last 12 months" in text:
            return "historical_actual"
        if "target" in text or "expected" in text:
            return "target"
        if "current" in text:
            return "current_claim"
        return "availability_claim"

    if field_name == "incident_notification_time":
        if "sla" in text or "contractual" in text:
            return "sla_commitment"
        if "target" in text or "expected" in text:
            return "target"
        if "may extend" in text or "team dependent" in text or "subject to" in text:
            return "conditional_commitment"
        return "response_commitment"

    if field_name == "data_residency":
        if "backup" in text or "backups" in text:
            return "backup_residency_claim"
        return "residency_claim"

    if field_name == "security_certifications":
        if "certified" in text or "certification" in text:
            return "certification_claim"
        if "in progress" in text or "working toward" in text or "aligned" in text:
            return "alignment_claim"
        return "security_claim"

    return "generic_claim"


def classify_time_basis(field_name: str, text: str) -> Optional[str]:
    if "rolling 12-month" in text or "rolling 12 month" in text or "last 12 months" in text:
        return "rolling_12_month"

    if "monthly" in text or "per month" in text:
        return "monthly"

    if "annual" in text or "yearly" in text or "per year" in text:
        return "annual"

    if "quarterly" in text or "per quarter" in text:
        return "quarterly"

    if "current" in text or "currently" in text:
        return "current"

    if field_name == "incident_notification_time":
        return None

    return None


def classify_scope(field_name: str, text: str) -> Optional[str]:
    if field_name == "operational_availability":
        if "critical service" in text or "critical services" in text:
            return "critical_services"
        if "platform" in text:
            return "platform"
        if "service" in text:
            return "service"
        if "global" in text:
            return "global"
        return None

    if field_name == "incident_notification_time":
        if "critical incident" in text or "critical incidents" in text:
            return "critical_incidents"
        if "all incidents" in text:
            return "all_incidents"
        return None

    if field_name == "data_residency":
        if "backup" in text or "backups" in text:
            return "backup_data"
        if "customer data" in text:
            return "customer_data"
        return None

    if field_name == "security_certifications":
        if "partial" in text:
            return "partial_coverage"
        if "enterprise-wide" in text or "all systems" in text:
            return "broad_coverage"
        return None

    return None


def classify_certification_status(text: str) -> Optional[str]:
    if "expired" in text or "lapsed" in text:
        return "expired"

    if "certified" in text or "holds" in text or "achieved" in text:
        return "certified"

    if "in progress" in text or "working toward" in text or "pursuing" in text:
        return "in_progress"

    if "aligned" in text or "alignment" in text:
        return "aligned"

    if "partial" in text:
        return "partial"

    return None


def classify_commitment_strength(metric_kind: str, binding_strength: str) -> str:
    """
    A slightly higher-level normalized commitment descriptor.
    """

    if metric_kind in {"sla_commitment", "response_commitment"} and binding_strength == "strong":
        return "firm"

    if metric_kind in {"target", "conditional_commitment", "alignment_claim"}:
        return "weak"

    if binding_strength == "weak":
        return "weak"

    return "moderate"


def classify_field_claim(field_name: str, field: Dict[str, Any]) -> Dict[str, Any]:
    text = _safe_text(field)

    binding_strength = classify_binding_strength(text)
    metric_kind = classify_metric_kind(field_name, text)
    time_basis = classify_time_basis(field_name, text)
    scope = classify_scope(field_name, text)

    claim: Dict[str, Any] = {
        "field": field_name,
        "raw_text": text if text else None,
        "metric_kind": metric_kind,
        "time_basis": time_basis,
        "scope": scope,
        "binding_strength": binding_strength,
        "commitment_strength": classify_commitment_strength(metric_kind, binding_strength),
    }

    if field_name == "security_certifications":
        claim["certification_status"] = classify_certification_status(text)

    return claim


def classify_all_claims(evidence: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    reviewable_fields = [
        "operational_availability",
        "incident_notification_time",
        "data_residency",
        "security_certifications",
    ]

    results: Dict[str, Dict[str, Any]] = {}

    for field_name in reviewable_fields:
        field = evidence.get(field_name)
        if not field:
            continue

        results[field_name] = classify_field_claim(field_name, field)

    return results