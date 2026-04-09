# app/core/validation/drift_detector.py

def detect_drift(pages: list, extracted: dict):
    """
    Simple drift detection:
    - Missing expected fields
    - Missing expected keywords
    """

    drift_flags = []

    # -------------------------
    # 1. Missing expected fields
    # -------------------------
    if not extracted.get("operational_availability"):
        drift_flags.append("Missing availability data")

    if not extracted.get("incident_notification_time"):
        drift_flags.append("Missing incident response data")

    # -------------------------
    # 2. Keyword check
    # -------------------------
    combined_text = " ".join(
    p if isinstance(p, str) else p.get("text", "")
    for p in pages
).lower()

    keywords = ["uptime", "availability", "incident", "response"]

    found = any(k in combined_text for k in keywords)

    if not found:
        drift_flags.append("No expected SLA keywords found")

    # -------------------------
    # 3. Result
    # -------------------------
    if drift_flags:
        return {
            "drift_detected": True,
            "issues": drift_flags
        }

    return {
        "drift_detected": False
    }