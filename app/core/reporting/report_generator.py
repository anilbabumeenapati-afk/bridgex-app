import json
import os
import csv


def generate_json_report(dpm_output):
    os.makedirs("output", exist_ok=True)

    csv_path = "output/report.csv"
    metadata_path = "output/metadata.json"

    # 🔥 WRITE CSV
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        # ✅ UPDATED HEADER
        writer.writerow(["field", "min", "max", "unit", "risk_flags"])

        for field, val in dpm_output.items():
            value = val.get("value", {})
            unit = val.get("unit", "")
            risk_flags = val.get("risk_flags", [])

            # convert list → string
            risk_flags_str = ";".join(risk_flags) if risk_flags else ""

            writer.writerow([
                field,
                value.get("min"),
                value.get("max"),
                unit,
                risk_flags_str
            ])

    # 🔥 WRITE METADATA
    with open(metadata_path, "w") as f:
        json.dump({
            "report_type": "DORA_POC",
            "fields": list(dpm_output.keys()),
            "columns": ["field", "min", "max", "unit", "risk_flags"]
        }, f, indent=2)

    return {
        "csv": csv_path,
        "metadata": metadata_path
    }