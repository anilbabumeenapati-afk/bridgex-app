import csv
import json
import os


def generate_xbrl_csv(dpm_output, entity, period, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "report.csv")
    metadata_path = os.path.join(output_dir, "metadata.json")

    rows = []

    for dpm_id, data in dpm_output.items():
        value = data.get("value", {})

        row = {
            "entity": entity,
            "period": period,
            "metric": dpm_id,
            "min": value.get("min"),
            "max": value.get("max"),
            "unit": data.get("unit")
        }

        rows.append(row)

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["entity", "period", "metric", "min", "max", "unit"]
        )
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "documentInfo": {
            "documentType": "https://xbrl.org/2021/xbrl-csv",
            "taxonomy": ["https://example.com/dpm-taxonomy"]
        },
        "tableTemplates": {
            "dpm_table": {
                "dimensions": {
                    "entity": "$entity",
                    "period": "$period"
                },
                "columns": {
                    "metric": {},
                    "min": {},
                    "max": {},
                    "unit": {}
                }
            }
        },
        "tables": {
            "dpm_table": {
                "template": "dpm_table",
                "url": "report.csv"
            }
        }
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return {
        "csv": csv_path,
        "metadata": metadata_path
    }