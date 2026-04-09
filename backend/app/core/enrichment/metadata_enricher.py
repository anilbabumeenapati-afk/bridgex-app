from typing import Any, Dict


def enrich_evidence(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """
    UI/display-oriented enrichment only.

    This function must NOT override core decision semantics.
    It should only derive lightweight metadata from already-computed fields:
    - lineage.confidence
    - trust.score
    - risk.flags
    - status
    """

    for field_name, field_data in evidence.items():
        if not isinstance(field_data, dict):
            continue

        # Skip non-field top-level objects
        if field_name in {"state", "vendor_profile"}:
            continue

        metadata = field_data.get("metadata") or {}
        lineage = field_data.get("lineage") or {}
        trust = field_data.get("trust") or {}
        risk = field_data.get("risk") or {}

        confidence = metadata.get("confidence")
        if confidence is None:
            confidence = lineage.get("confidence")

        trust_score = trust.get("score")
        risk_flags = risk.get("flags") or []
        status = field_data.get("status")

        # Priority should be driven primarily by trust/risk, not re-invented confidence
        if trust_score is not None:
            if trust_score < 60:
                priority = "high"
            elif trust_score < 80:
                priority = "medium"
            else:
                priority = "low"
        else:
            if confidence is not None and confidence < 0.8:
                priority = "high"
            else:
                priority = "medium"

        review_required = (
            status != "APPROVED"
            or len(risk_flags) > 0
            or (trust_score is not None and trust_score < 75)
        )

        metadata["confidence"] = confidence
        metadata["priority"] = priority
        metadata["review_required"] = review_required

        field_data["metadata"] = metadata

        # Backward-compatible alias for older UI/components if needed
        if "risk_flags" not in field_data:
            field_data["risk_flags"] = risk_flags

    return evidence