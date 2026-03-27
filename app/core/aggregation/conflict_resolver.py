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

# -------------------------
# DATA RESIDENCY
# -------------------------
def resolve_data_residency(candidates):
    if not candidates:
        return None

    values = []
    for c in candidates:
        if c.get("value"):
            values.append(c["value"])

    unique_values = list(set(values))
    conflict = len(unique_values) > 1

    # -------------------------
    # PRIORITY RULES
    # -------------------------
    selected = None

    for c in candidates:
        text = c["source_text"].lower()

        # Prefer explicit strong statements
        if "stored" in text or "hosted" in text:
            selected = c
            break

    if not selected:
        selected = candidates[0]

    result = selected.copy()

    # -------------------------
    # NORMALIZATION (SIMPLE FOR NOW)
    # -------------------------
    value_text = result["value"].lower()

    if "eu" in value_text or "europe" in value_text:
        result["normalized"] = "EU"
    elif "germany" in value_text:
        result["normalized"] = "DE"
    elif "france" in value_text:
        result["normalized"] = "FR"
    else:
        result["normalized"] = "UNKNOWN"

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
        result["confidence"] = 0.9

    return result

# -------------------------
# SECURITY CERTIFICATIONS
# -------------------------
def resolve_certifications(candidates):
    if not candidates:
        return None

    values = []
    for c in candidates:
        if c.get("value"):
            values.append(c["value"].upper().replace(" ", ""))

    unique_values = list(set(values))

    result = candidates[0].copy()

    # normalization
    result["normalized"] = {
        "certifications": unique_values
    }

    # conflict (not really conflict here, but multiple certs)
    result["conflict"] = {
        "detected": len(unique_values) > 1,
        "values": unique_values
    }

    result["confidence"] = 0.95

    return result