from typing import Any, Dict, List, Optional


def _get_field(evidence: Dict[str, Any], field_name: str) -> Optional[Dict[str, Any]]:
    field = evidence.get(field_name)
    if isinstance(field, dict):
        return field
    return None


def _get_claim(field: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not field:
        return {}
    metadata = field.get("metadata") or {}
    claim = metadata.get("claim") or {}
    return claim if isinstance(claim, dict) else {}


def _get_normalized(field: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not field:
        return {}
    normalized = field.get("normalized") or {}
    return normalized if isinstance(normalized, dict) else {}


def _get_source(field: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not field:
        return {}
    source = field.get("source") or {}
    if isinstance(source, dict):
        return source
    return {}


def _build_signal(
    signal_type: str,
    message: str,
    fields: List[str],
    details: Dict[str, Any],
    action: str = "clarification_suggested",
    level: str = "contextual_difference",
) -> Dict[str, Any]:
    return {
        "type": signal_type,
        "message": message,
        "fields": fields,
        "action": action,
        "level": level,
        "details": details,
    }


def _availability_vs_certifications(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []

    availability = _get_field(evidence, "operational_availability")
    certifications = _get_field(evidence, "security_certifications")

    if not availability or not certifications:
        return signals

    availability_claim = _get_claim(availability)
    cert_claim = _get_claim(certifications)

    availability_binding = availability_claim.get("binding_strength")
    cert_status = cert_claim.get("certification_status")

    if availability_binding == "strong" and cert_status in {"in_progress", "aligned", "partial"}:
        signals.append(
            _build_signal(
                signal_type="assurance_maturity_difference",
                message="Strong service commitments appear alongside less mature certification wording.",
                fields=["operational_availability", "security_certifications"],
                details={
                    "availability_binding_strength": availability_binding,
                    "certification_status": cert_status,
                    "availability_source": _get_source(availability),
                    "certification_source": _get_source(certifications),
                },
                action="clarification_suggested",
                level="contextual_difference",
            )
        )

    return signals


def _availability_vs_incident(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []

    availability = _get_field(evidence, "operational_availability")
    incident = _get_field(evidence, "incident_notification_time")

    if not availability or not incident:
        return signals

    availability_claim = _get_claim(availability)
    incident_claim = _get_claim(incident)

    availability_binding = availability_claim.get("binding_strength")
    incident_binding = incident_claim.get("binding_strength")

    availability_trust = ((availability.get("trust") or {}).get("score")) or 0
    incident_trust = ((incident.get("trust") or {}).get("score")) or 0

    if availability_binding == "strong" and incident_binding == "weak":
        signals.append(
            _build_signal(
                signal_type="commitment_profile_difference",
                message="Service availability commitments appear stronger than incident notification commitments.",
                fields=["operational_availability", "incident_notification_time"],
                details={
                    "availability_binding_strength": availability_binding,
                    "incident_binding_strength": incident_binding,
                    "availability_trust_score": availability_trust,
                    "incident_trust_score": incident_trust,
                },
                action="clarification_optional",
                level="multiple_interpretations",
            )
        )

    return signals


def _residency_vs_global_language(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []

    residency = _get_field(evidence, "data_residency")
    if not residency:
        return signals

    claim = _get_claim(residency)
    source_text = ((_get_source(residency).get("text")) or "").lower()
    normalized = _get_normalized(residency)

    normalized_min = normalized.get("min")
    normalized_max = normalized.get("max")

    # Keep this intentionally soft/neutral
    if (
        any(term in source_text for term in ["global", "globally", "outside eu", "backup", "backups"])
        and any(term in source_text for term in ["eu", "europe", "germany", "france"])
    ):
        signals.append(
            _build_signal(
                signal_type="residency_scope_clarification",
                message="Regional hosting language and broader storage scope language appear together.",
                fields=["data_residency"],
                details={
                    "normalized_value": {
                        "min": normalized_min,
                        "max": normalized_max,
                    },
                    "claim_scope": claim.get("scope"),
                    "source": _get_source(residency),
                },
                action="clarification_suggested",
                level="contextual_difference",
            )
        )

    return signals


def _missing_supporting_context(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []

    availability = _get_field(evidence, "operational_availability")
    incident = _get_field(evidence, "incident_notification_time")
    certifications = _get_field(evidence, "security_certifications")
    residency = _get_field(evidence, "data_residency")

    present_fields = {
        "operational_availability": bool(availability and availability.get("value")),
        "incident_notification_time": bool(incident and incident.get("value")),
        "security_certifications": bool(certifications and certifications.get("value")),
        "data_residency": bool(residency and residency.get("value")),
    }

    if present_fields["operational_availability"] and not present_fields["incident_notification_time"]:
        signals.append(
            _build_signal(
                signal_type="supporting_context_gap",
                message="Availability information is present, while incident timing evidence is not yet present.",
                fields=["operational_availability", "incident_notification_time"],
                details={"present_fields": present_fields},
                action="clarification_optional",
                level="coverage_gap",
            )
        )

    if present_fields["operational_availability"] and not present_fields["security_certifications"]:
        signals.append(
            _build_signal(
                signal_type="supporting_context_gap",
                message="Availability information is present, while certification evidence is not yet present.",
                fields=["operational_availability", "security_certifications"],
                details={"present_fields": present_fields},
                action="clarification_optional",
                level="coverage_gap",
            )
        )

    return signals


def detect_cross_field_signals(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Neutral, vendor-safe cross-field interpretation engine.

    Output is intentionally framed as:
    - contextual differences
    - clarification suggestions
    - coverage gaps

    not:
    - vendor error
    - contradiction accusation
    """
    signals: List[Dict[str, Any]] = []

    signals.extend(_availability_vs_certifications(evidence))
    signals.extend(_availability_vs_incident(evidence))
    signals.extend(_residency_vs_global_language(evidence))
    signals.extend(_missing_supporting_context(evidence))

    return signals