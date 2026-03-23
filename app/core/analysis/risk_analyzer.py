def analyze_availability(field: dict):
    risks = []
    trace = []

    text = field.get("lineage", {}).get("raw_text", "").lower()
    conflict = field.get("lineage", {}).get("conflict", {})

    if conflict.get("detected"):
        risks.append("SOURCE_CONTRADICTION")
        trace.append("Multiple values detected in document")

    if "between" in text or "-" in text:
        risks.append("HIGH_VARIANCE")
        trace.append("Range detected in source text")

    if "approx" in text or "realistically" in text:
        risks.append("NON_COMMITTED_VALUE")
        trace.append("Non-committed wording detected")

    return {
        "flags": risks,
        "trace": trace
    }


def analyze_incident(field: dict):
    risks = []

    text = field.get("lineage", {}).get("raw_text", "").lower()

    if "team dependent" in text:
        risks.append("CONDITIONAL_RESPONSE")

    if "may extend" in text:
        risks.append("NON_STRICT_SLA")

    return risks