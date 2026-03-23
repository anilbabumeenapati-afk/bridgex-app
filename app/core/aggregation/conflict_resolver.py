from app.core.normalization.availability_normalizer import normalize_availability
from app.core.normalization.time_normalizer import normalize_time


# -------------------------
# AVAILABILITY
# -------------------------
def resolve_availability(candidates):
    if not candidates:
        return None

    values = []
    for c in candidates:
        if c.get("value"):
            values.append(c["value"])

    unique_values = list(set(values))
    conflict = len(unique_values) > 1

    # -------------------------
    # PRIORITY RULES (UNCHANGED)
    # -------------------------
    selected = None

    for c in candidates:
        if "target" in c["source_text"].lower():
            selected = c
            break

    if not selected:
        for c in candidates:
            if "uptime" in c["source_text"].lower():
                selected = c
                break

    if not selected:
        selected = candidates[0]

    result = selected.copy()

    # -------------------------
    # NORMALIZATION
    # -------------------------
    result["normalized"] = normalize_availability(result["value"])

    # -------------------------
    # CONFLICT HANDLING
    # -------------------------
    if conflict:
        result["conflict"] = {
            "detected": True,
            "values": unique_values
        }
        result["confidence"] = 0.6  # reduce confidence
    else:
        result["conflict"] = {
            "detected": False
        }
        result["confidence"] = 0.95

    return result


# -------------------------
# INCIDENT TIME
# -------------------------
def resolve_incident_time(candidates):
    if not candidates:
        return None

    values = []
    for c in candidates:
        if c.get("value"):
            values.append(c["value"])

    unique_values = list(set(values))
    conflict = len(unique_values) > 1

    # -------------------------
    # PRIORITY RULES (UNCHANGED)
    # -------------------------
    selected = None

    for c in candidates:
        if "critical" in c["source_text"].lower():
            selected = c
            break

    if not selected:
        for c in candidates:
            if "target" in c["source_text"].lower():
                selected = c
                break

    if not selected:
        selected = candidates[0]

    result = selected.copy()

    # -------------------------
    # NORMALIZATION
    # -------------------------
    result["normalized"] = normalize_time(result["value"])

    # -------------------------
    # CONFLICT HANDLING
    # -------------------------
    if conflict:
        result["conflict"] = {
            "detected": True,
            "values": unique_values
        }
        result["confidence"] = 0.6
    else:
        result["conflict"] = {
            "detected": False
        }
        result["confidence"] = 0.95

    return result