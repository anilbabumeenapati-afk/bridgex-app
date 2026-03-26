def enrich_evidence(evidence: dict):
    for field_name, field_data in evidence.items():

        if not field_data:
            continue

        # -------------------------
        # RISK ANALYSIS (FIXED)
        # -------------------------
        if field_name == "operational_availability":
            analysis = analyze_availability(field_data)
            field_data["risk_flags"] = analysis.get("risk_flags", [])

        elif field_name == "incident_notification_time":
            field_data["risk_flags"] = analyze_incident(field_data)

        # -------------------------
        # CONFIDENCE
        # -------------------------
        normalized = field_data.get("normalized")
        confidence = 0.9

        if not normalized:
            confidence = 0.3
        elif normalized.get("min") != normalized.get("max"):
            confidence = 0.7

        # -------------------------
        # METADATA
        # -------------------------
        field_data["metadata"] = {
            "confidence": confidence,
            "priority": "high",
            "review_required": confidence < 0.8
        }

    return evidence