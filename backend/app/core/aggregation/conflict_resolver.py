from app.core.normalization.availability_normalizer import normalize_availability
from app.core.normalization.time_normalizer import normalize_time


# -------------------------
# AVAILABILITY
# -------------------------
def resolve_availability(candidates):
    if not candidates:
        return None

    valid = [c for c in candidates if c.get("value")]
    if not valid:
        return None

    # Build signatures for conflict detection
    signatures = [
        (
            c.get("normalized", {}).get("min"),
            c.get("normalized", {}).get("max"),
        )
        for c in valid
    ]

    unique = list(set(signatures))
    conflict = len(unique) > 1

    def rank(c):
        text = (c.get("source_text") or "").lower()
        context_score = c.get("context_score", 0)

        strength = 0
        if "sla" in text or "guarantee" in text:
            strength += 2
        elif "target" in text or "expected" in text:
            strength += 0

        if "current" in text:
            strength += 1
        if "historical" in text:
            strength -= 1

        return (context_score, strength)

    selected = sorted(valid, key=rank, reverse=True)[0]

    result = selected.copy()
    result["source_file"] = selected.get("source_file", "unknown")

    if conflict:
        result["conflict"] = {
            "detected": True,
            "values": [
                {
                    "raw": c.get("value"),
                    "normalized": c.get("normalized"),
                    "source_text": c.get("source_text"),
                    "page": c.get("page"),
                }
                for c in valid
            ]
        }
        result["confidence"] = 0.6
    else:
        result["conflict"] = {"detected": False}
        result["confidence"] = 0.95

    return result

# -------------------------
# INCIDENT TIME
# -------------------------
def resolve_incident_time(candidates):
    if not candidates:
        return None

    # Keep only candidates that actually have a value
    valid_candidates = [c for c in candidates if c.get("value")]
    if not valid_candidates:
        return None

    # Build comparable normalized signatures
    normalized_signatures = []
    for c in valid_candidates:
        normalized = c.get("normalized") or {}
        signature = (
            normalized.get("min"),
            normalized.get("max"),
            normalized.get("unit"),
        )
        normalized_signatures.append(signature)

    unique_signatures = list(set(normalized_signatures))
    conflict = len(unique_signatures) > 1

    # -------------------------
    # PRIORITY RULES
    # -------------------------
    # Stronger candidates first:
    # 1. higher context_score
    # 2. has explicit time qualifier
    # 3. stronger wording in source text
    # 4. fallback to original order
    def candidate_rank(c):
        text = (c.get("source_text") or "").lower()
        context_score = c.get("context_score", 0)
        has_time_qualifier = 1 if c.get("has_time_qualifier") else 0

        strong_wording = 0
        if "shall" in text or "must" in text:
            strong_wording = 2
        elif "within" in text or "no later than" in text:
            strong_wording = 1

        return (
            context_score,
            has_time_qualifier,
            strong_wording,
        )

    selected = sorted(valid_candidates, key=candidate_rank, reverse=True)[0]

    result = selected.copy()
    result["source_file"] = selected.get("source_file", "unknown")

    # Ensure normalized is preserved
    normalized = selected.get("normalized")
    if normalized:
        result["normalized"] = normalized
    else:
        # Fallback if older extractor returns only raw value
        result["normalized"] = normalize_time(result["value"])

    # -------------------------
    # CONFLICT HANDLING
    # -------------------------
    if conflict:
        result["conflict"] = {
            "detected": True,
            "values": [
                {
                    "raw": c.get("value"),
                    "normalized": c.get("normalized"),
                    "page": c.get("page"),
                    "source_text": c.get("source_text"),
                    "source_file": c.get("source_file", "unknown"),
                }
                for c in valid_candidates
            ],
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
    result["source_file"] = selected.get("source_file", "unknown")

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

    result["source_file"] = candidates[0].get("source_file", "unknown")

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