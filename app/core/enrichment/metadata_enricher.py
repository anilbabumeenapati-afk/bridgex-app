def enrich_evidence(evidence: dict):
    for field_name, field_data in evidence.items():

        if not field_data:
            continue

        normalized = field_data.get("normalized")

        # -------------------------
        # CONFIDENCE SCORE
        # -------------------------
        confidence = 0.9

        if not normalized:
            confidence = 0.3
        elif normalized.get("min") != normalized.get("max"):
            confidence = 0.7

        # -------------------------
        # PRIORITY
        # -------------------------
        if field_name == "operational_availability":
            priority = "high"
        elif field_name == "incident_notification_time":
            priority = "high"
        else:
            priority = "medium"

        # -------------------------
        # ATTACH METADATA
        # -------------------------
        field_data["metadata"] = {
            "confidence": confidence,
            "priority": priority,
            "review_required": confidence < 0.8
        }

    return evidence