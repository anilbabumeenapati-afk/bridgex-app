from typing import Any, Dict, List, Optional, Tuple


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _normalize_item(item: Any) -> Dict[str, Any]:
    """
    Force every candidate into dict format
    """
    if isinstance(item, dict):
        return item

    if isinstance(item, str):
        return {
            "raw": item,
            "normalized": {},
            "source_text": item,
        }

    return {}


def _norm_signature(item: Any) -> Tuple[Any, Any, Any]:
    item = _normalize_item(item)
    normalized = _safe_dict(item.get("normalized"))

    return (
        normalized.get("min"),
        normalized.get("max"),
        normalized.get("unit"),
    )


def _raw_signature(item: Any) -> Tuple[Any, Any]:
    item = _normalize_item(item)

    return (
        item.get("raw"),
        item.get("source_text"),
    )


def _dedupe_candidates(values: List[Any]) -> List[Dict[str, Any]]:
    seen = set()
    deduped = []

    for raw_item in values:
        item = _normalize_item(raw_item)

        norm_sig = _norm_signature(item)
        raw_sig = _raw_signature(item)
        sig = (norm_sig, raw_sig)

        if sig in seen:
            continue

        seen.add(sig)
        deduped.append(item)

    return deduped


def _format_value(item: Dict[str, Any]) -> str:
    normalized = _safe_dict(item.get("normalized"))

    min_val = normalized.get("min")
    max_val = normalized.get("max")
    unit = normalized.get("unit")

    if min_val is None and max_val is None:
        return str(item.get("raw") or "unknown")

    if min_val == max_val:
        return f"{min_val} {unit or ''}".strip()

    return f"{min_val}-{max_val} {unit or ''}".strip()


def _summarize_resolver_conflict(field: str, details: Dict[str, Any]) -> Dict[str, Any]:
    values = _safe_list(details.get("values"))
    deduped = _dedupe_candidates(values)

    formatted = [_format_value(v) for v in deduped]

    primary = formatted[0] if formatted else None
    alternates = formatted[1:] if len(formatted) > 1 else []

    if details.get("detected") is False:
        return {
            "field": field,
            "severity": "low",
            "headline": "No material conflict detected",
            "primary_value": primary,
            "alternate_values": alternates,
            "explanation": "Multiple mentions exist but no conflicting values detected",
        }

    if len(deduped) <= 1:
        return {
            "field": field,
            "severity": "low",
            "headline": "Single value detected",
            "primary_value": primary,
            "alternate_values": [],
            "explanation": "No ambiguity detected",
        }

    if "incident" in field:
        return {
            "field": field,
            "severity": "medium",
            "headline": "Multiple incident-related timings detected",
            "primary_value": primary,
            "alternate_values": alternates,
            "explanation": "Likely different scopes (response vs resolution vs support)",
        }

    if "availability" in field:
        return {
            "field": field,
            "severity": "medium",
            "headline": "Multiple availability figures detected",
            "primary_value": primary,
            "alternate_values": alternates,
            "explanation": "May represent target vs actual vs conditional statements",
        }

    return {
        "field": field,
        "severity": "medium",
        "headline": "Multiple values detected",
        "primary_value": primary,
        "alternate_values": alternates,
        "explanation": "Field contains more than one value",
    }


def summarize_conflict_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None

    field = item.get("field", "unknown")
    conflict_type = item.get("type")
    details = _safe_dict(item.get("details"))

    if conflict_type == "resolver_conflict":
        return _summarize_resolver_conflict(field, details)

    return {
        "field": field,
        "severity": "medium",
        "headline": str(conflict_type or "conflict"),
        "primary_value": None,
        "alternate_values": [],
        "explanation": "Conflict detected, review required",
    }


def summarize_conflicts(conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []

    for item in conflicts:
        summary = summarize_conflict_item(item)
        if summary:
            results.append(summary)

    return results