def build_passport(field):
    if not field:
        return None

    source = field.get("source") or {}
    lineage = field.get("lineage") or {}
    risk = field.get("risk") or {}
    trust = field.get("trust") or {}
    review = field.get("review") or {}
    metadata = field.get("metadata") or {}

    passport = {
        # Keep this compatible with current dpm_mapper.py
        "normalized": field.get("normalized"),

        # Preserve old top-level compatibility where useful
        "confidence": metadata.get("confidence", lineage.get("confidence")),
        "conflict": lineage.get("conflict"),

        # Backward-compatible alias for current mapper
        "risk_flags": risk.get("flags", field.get("risk_flags", [])),

        # Decision now comes from review, not lineage
        "decision": review.get("decision"),

        # Keep mapped field from lineage
        "mapped_field": lineage.get("mapped_field"),

        # Source trace
        "source": {
            "raw_text": source.get("text") or field.get("source_text") or lineage.get("raw_text"),
            "page": source.get("page") or field.get("page") or lineage.get("page"),
            "file": source.get("file") or lineage.get("source_file"),
            "rule": lineage.get("extraction_rule"),
        },

        # New richer trust block
        "trust": {
            "score": trust.get("score"),
            "verification_tier": trust.get("verification_tier"),
            "binding_strength": trust.get("binding_strength"),
            "source_type": trust.get("source_type"),
            "staleness_status": trust.get("staleness_status"),
        },

        # Optional semantic claim metadata
        "claim": metadata.get("claim"),

        # Keep status visible
        "status": field.get("status"),
    }

    return passport