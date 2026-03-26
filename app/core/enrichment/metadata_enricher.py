def enrich_evidence(evidence: dict):
    for field_name, field_data in evidence.items():

        if not field_data:
            continue

        normalized = field_data.get("normalized")

        # -------------------------
        # 🔥 RUN RISK ANALYSIS
        # -------------------------
        if field_name == "operational_availability":
            analysis = analyze_availability(field_data)
            field_data = analysis  # updated field

        elif field_name == "incident_notification_time":
            field_data = analyze_incident(field_data)

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
        if field_name in ["operational_availability", "incident_notification_time"]:
            priority = "high"
        else:
            priority = "medium"

        # -------------------------
        # ATTACH METADATA
        # -------------------------
        field_data["metadata"] = {
            "confidence": confidence,
            "priority": priority,
            "review_required": (
                confidence < 0.8 or len(field_data.get("risk_flags", [])) > 0
            )
        }

        # 🔥 ENSURE WRITE BACK
        evidence[field_name] = field_data
        print("ENRICHED FIELD:", field_name, field_data.get("risk_flags"))

    return evidence