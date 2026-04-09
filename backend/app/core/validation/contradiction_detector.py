from typing import Any, Dict, List, Optional


def _extract_numeric_pair(field: Dict[str, Any]) -> Dict[str, Any]:
    normalized = field.get("normalized") or {}
    value = field.get("value")

    if isinstance(normalized, dict):
        return {
            "min": normalized.get("min"),
            "max": normalized.get("max"),
            "unit": normalized.get("unit"),
        }

    if isinstance(value, dict):
        return {
            "min": value.get("min"),
            "max": value.get("max"),
            "unit": value.get("unit"),
        }

    return {
        "min": None,
        "max": None,
        "unit": None,
    }


def _values_differ(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return (
        a.get("min") != b.get("min")
        or a.get("max") != b.get("max")
        or a.get("unit") != b.get("unit")
    )


def compare_claims(
    field_name: str,
    current_field: Dict[str, Any],
    current_claim: Dict[str, Any],
    previous_field: Optional[Dict[str, Any]] = None,
    previous_claim: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Returns a list of contradiction / mismatch records.

    This compares:
    - current normalized field values vs previous values
    - claim semantics: metric_kind, time_basis, scope, binding_strength
    """

    issues: List[Dict[str, Any]] = []

    current_conflict = (current_field.get("lineage") or {}).get("conflict") or {}
    if current_conflict.get("detected"):
        issues.append(
            {
                "field": field_name,
                "conflict_type": "intra_document_conflict",
                "severity": "medium",
                "details": {
                    "values": current_conflict.get("values", []),
                },
            }
        )

    if not previous_field or not previous_claim:
        return issues

    current_value = _extract_numeric_pair(current_field)
    previous_value = _extract_numeric_pair(previous_field)

    current_metric_kind = current_claim.get("metric_kind")
    previous_metric_kind = previous_claim.get("metric_kind")

    current_time_basis = current_claim.get("time_basis")
    previous_time_basis = previous_claim.get("time_basis")

    current_scope = current_claim.get("scope")
    previous_scope = previous_claim.get("scope")

    current_binding = current_claim.get("binding_strength")
    previous_binding = previous_claim.get("binding_strength")

    # 1. Exact contradiction: same semantic context, different values
    same_semantic_context = (
        current_metric_kind == previous_metric_kind
        and current_time_basis == previous_time_basis
        and current_scope == previous_scope
    )

    if same_semantic_context and _values_differ(current_value, previous_value):
        issues.append(
            {
                "field": field_name,
                "conflict_type": "direct_value_contradiction",
                "severity": "high",
                "details": {
                    "current": current_value,
                    "previous": previous_value,
                    "metric_kind": current_metric_kind,
                    "time_basis": current_time_basis,
                    "scope": current_scope,
                },
            }
        )

    # 2. Same field, different time basis
    if current_time_basis != previous_time_basis and _values_differ(current_value, previous_value):
        issues.append(
            {
                "field": field_name,
                "conflict_type": "temporal_mismatch",
                "severity": "medium",
                "details": {
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "current_time_basis": current_time_basis,
                    "previous_time_basis": previous_time_basis,
                },
            }
        )

    # 3. Same field, different metric kind
    if current_metric_kind != previous_metric_kind and _values_differ(current_value, previous_value):
        issues.append(
            {
                "field": field_name,
                "conflict_type": "metric_kind_mismatch",
                "severity": "medium",
                "details": {
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "current_metric_kind": current_metric_kind,
                    "previous_metric_kind": previous_metric_kind,
                },
            }
        )

    # 4. Same field, different scope
    if current_scope != previous_scope and _values_differ(current_value, previous_value):
        issues.append(
            {
                "field": field_name,
                "conflict_type": "scope_mismatch",
                "severity": "medium",
                "details": {
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "current_scope": current_scope,
                    "previous_scope": previous_scope,
                },
            }
        )

    # 5. Same value, but commitment strength downgraded/upgraded
    if not _values_differ(current_value, previous_value) and current_binding != previous_binding:
        issues.append(
            {
                "field": field_name,
                "conflict_type": "commitment_strength_change",
                "severity": "low",
                "details": {
                    "value": current_value,
                    "current_binding_strength": current_binding,
                    "previous_binding_strength": previous_binding,
                },
            }
        )

    # 6. Special certification handling
    if field_name == "security_certifications":
        current_status = current_claim.get("certification_status")
        previous_status = previous_claim.get("certification_status")

        if current_status and previous_status and current_status != previous_status:
            issues.append(
                {
                    "field": field_name,
                    "conflict_type": "certification_status_change",
                    "severity": "high" if "certified" in {current_status, previous_status} else "medium",
                    "details": {
                        "current_status": current_status,
                        "previous_status": previous_status,
                    },
                }
            )

    return issues