def build_passport(field):
    if not field:
        return None

    lineage = field.get("lineage", {})

    passport = {
        "value": field.get("normalized"),
        "confidence": lineage.get("confidence") if lineage else None,
        "conflict": lineage.get("conflict") if lineage else None,

        # 🔥 FIXED (reads from field directly)
        "risk_flags": field.get("risk_flags", []),

        "decision": lineage.get("decision") if lineage else None,
        "mapped_field": lineage.get("mapped_field") if lineage else None,

        "source": {
            "raw_text": lineage.get("raw_text") if lineage else None,
            "page": lineage.get("page") if lineage else None,
            "rule": lineage.get("extraction_rule") if lineage else None
        }
    }

    return passport