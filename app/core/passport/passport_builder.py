def build_passport(field):
    if not field:
        return None

    lineage = field.get("lineage", {})

    passport = {
        "value": field.get("normalized"),
        "confidence": lineage.get("confidence"),
        "conflict": lineage.get("conflict"),
        "risk_flags": field.get("risk_flags") or lineage.get("risk_flags", []),
        "decision": lineage.get("decision"),
        "mapped_field": lineage.get("mapped_field"),
        "source": {
            "raw_text": lineage.get("raw_text"),
            "page": lineage.get("page"),
            "rule": lineage.get("extraction_rule")
        }
    }

    return passport