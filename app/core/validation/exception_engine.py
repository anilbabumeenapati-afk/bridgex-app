UNCERTAINTY_TERMS = [
    "usually", "approx", "approximately",
    "realistically", "subject to", "may",
    "target", "expected", "indicative"
]


def detect_uncertainty(text: str):
    if not text:
        return None

    for term in UNCERTAINTY_TERMS:
        if term in text.lower():
            return term

    return None


def build_exceptions(evidence: dict):
    exceptions = []

    for field_name, field_data in evidence.items():

        if not field_data:
            continue

        normalized = field_data.get("normalized")
        lineage = field_data.get("lineage", {})
        source_text = lineage.get("source_text", "")

        # -------------------------
        # 1. MISSING VALUE
        # -------------------------
        if not normalized:
            exceptions.append({
                "field": field_name,
                "issue": "missing_value",
                "severity": "high",
                "action_required": "manual_review"
            })
            continue

        # -------------------------
        # 2. UNCERTAINTY DETECTION
        # -------------------------
        term = detect_uncertainty(source_text)

        if term:
            exceptions.append({
                "field": field_name,
                "issue": "non_binding_language",
                "details": f"contains '{term}'",
                "severity": "medium",
                "action_required": "review_required"
            })

        # -------------------------
        # 3. INVALID VALUES
        # -------------------------
        min_val = normalized.get("min")
        max_val = normalized.get("max")

        if min_val is None or max_val is None:
            exceptions.append({
                "field": field_name,
                "issue": "invalid_structure",
                "severity": "high",
                "action_required": "fix_extraction"
            })

        # -------------------------
        # 4. RANGE CONFLICT
        # -------------------------
        if min_val and max_val and min_val > max_val:
            exceptions.append({
                "field": field_name,
                "issue": "range_conflict",
                "details": f"min {min_val} > max {max_val}",
                "severity": "high"
            })

    return exceptions
    
        