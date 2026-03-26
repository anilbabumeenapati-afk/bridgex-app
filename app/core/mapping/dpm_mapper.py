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
        # MAP FIELD → DPM
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
        # ✅ CORRECT VALUE SOURCE
        # -------------------------
        normalized = field_data.get("normalized") or {}

        if not isinstance(normalized, dict):
            print(f"❌ Invalid normalized for {field_name}: {normalized}")
            continue

        # -------------------------
        # BUILD OUTPUT
        # -------------------------
        result[config["dpm_id"]] = {
            "value": {
                "min": normalized.get("min"),
                "max": normalized.get("max")
            },
            "unit": config.get("unit"),
            "risk_flags": (field_data.get("risk_flags")
                        or field_data.get("metadata", {}).get("risk_flags", []))
        }

    print("DPM OUTPUT:", result)
    return result