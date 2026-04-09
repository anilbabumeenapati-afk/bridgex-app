import json
import os
import csv


def generate_json_report(dpm_output):
    os.makedirs("output", exist_ok=True)

    csv_path = "output/report.csv"
    metadata_path = "output/metadata.json"

    # -------------------------
    # WRITE CSV
    # Keep backward-compatible CSV contract
    # -------------------------
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["field", "min", "max", "unit", "risk_flags"])

        for field, val in dpm_output.items():
            value = val.get("value", {}) or {}
            unit = val.get("unit", "")
            risk_flags = val.get("risk_flags", [])

            risk_flags_str = ";".join(risk_flags) if risk_flags else ""

            writer.writerow([
                field,
                value.get("min"),
                value.get("max"),
                unit,
                risk_flags_str
            ])

    # -------------------------
    # WRITE METADATA
    # Enrich metadata using newer mapped object shape
    # -------------------------
    field_metadata = {}

    for field, val in dpm_output.items():
        field_metadata[field] = {
            "unit": val.get("unit"),
            "risk_flags": val.get("risk_flags", []),
            "trust_score": val.get("trust_score"),
            "binding_strength": val.get("binding_strength"),
            "verification_tier": val.get("verification_tier"),
            "status": val.get("status"),
            "source": val.get("source"),
            "claim": val.get("claim"),
        }

    metadata = {
        "report_type": "DORA_POC",
        "fields": list(dpm_output.keys()),
        "columns": ["field", "min", "max", "unit", "risk_flags"],
        "field_metadata": field_metadata,
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return {
        "csv": csv_path,
        "metadata": metadata_path
    }