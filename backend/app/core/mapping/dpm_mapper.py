from app.core.mapping.dpm_registry import DPM_REGISTRY, FIELD_MAPPING


def map_to_dpm(passport):
    print("STEP 3 - PASSPORT INPUT:", passport)
    result = {}

    for field_name, field_data in passport.items():
        if not field_data:
            print(f"⚠ Skipping empty field: {field_name}")
            continue

        print("STEP 4 - FIELD:", field_name)
        print("FIELD DATA:", field_data)

        # -------------------------
        # MAP FIELD -> DPM
        # -------------------------
        dpm_field = FIELD_MAPPING.get(field_name)
        if not dpm_field:
            print(f"⚠ No mapping for: {field_name}")
            continue

        config = DPM_REGISTRY.get(dpm_field)
        if not config:
            print(f"⚠ No config for: {dpm_field}")
            continue

        # -------------------------
        # READ NORMALIZED VALUE
        # -------------------------
        normalized = field_data.get("normalized") or {}

        if not isinstance(normalized, dict):
            print(f"❌ Invalid normalized for {field_name}: {normalized}")
            continue

        value_min = normalized.get("min")
        value_max = normalized.get("max")

        # -------------------------
        # READ SUPPORTING METADATA
        # -------------------------
        risk_flags = field_data.get("risk_flags", [])

        trust = field_data.get("trust") or {}
        source = field_data.get("source") or {}
        claim = field_data.get("claim") or {}

        # -------------------------
        # BUILD OUTPUT
        # Keep contract compatible with report_generator.py
        # -------------------------
        result[config["dpm_id"]] = {
            "value": {
                "min": value_min,
                "max": value_max
            },
            "unit": config.get("unit"),
            "risk_flags": risk_flags,

            # richer metadata for future validator / metadata JSON
            "trust_score": trust.get("score"),
            "binding_strength": trust.get("binding_strength"),
            "verification_tier": trust.get("verification_tier"),
            "source": {
                "raw_text": source.get("raw_text"),
                "page": source.get("page"),
                "file": source.get("file"),
                "rule": source.get("rule"),
            },
            "claim": claim,
            "status": field_data.get("status"),
        }

    print("DPM OUTPUT:", result)
    return result