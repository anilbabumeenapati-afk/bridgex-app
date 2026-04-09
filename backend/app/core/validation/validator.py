from app.core.mapping.dpm_registry import DPM_REGISTRY, FIELD_MAPPING

def validate_all(evidence):
    result = {
        "status": "valid",
        "fields": {}
    }

    for field_name, field_data in evidence.items():

        dpm_field = FIELD_MAPPING.get(field_name)

        if not dpm_field:
            result["fields"][field_name] = {"status": "skipped"}
            continue

        config = DPM_REGISTRY.get(dpm_field)

        if not config:
            result["fields"][field_name] = {"status": "skipped"}
            continue

        normalized = field_data.get("normalized")

        # 🔥 FIXED MISSING CHECK
        if not isinstance(normalized, dict):
            result["fields"][field_name] = {"status": "missing"}
            result["status"] = "invalid"
            continue

        min_val = normalized.get("min")
        max_val = normalized.get("max")

        if min_val is None and max_val is None:
            result["fields"][field_name] = {"status": "missing"}
            result["status"] = "invalid"
            continue

        rules = config.get("validation", {})
        errors = []

        if "min" in rules and min_val is not None:
            if min_val < rules["min"]:
                errors.append(f"min {min_val} < allowed {rules['min']}")

        if "max" in rules and max_val is not None:
            if max_val > rules["max"]:
                errors.append(f"max {max_val} > allowed {rules['max']}")

        if errors:
            result["fields"][field_name] = {
                "status": "fail",
                "errors": errors
            }
            result["status"] = "invalid"
        else:
            result["fields"][field_name] = {"status": "pass"}

    return result