import re

def normalize_availability(value: str):
    value = value.strip()

    # range: 98.9%–99.7%
    match = re.search(r"(\d{2,3}\.\d+)\s?[-–]\s?(\d{2,3}\.\d+)%", value)
    if match:
        return {
            "min": float(match.group(1)),
            "max": float(match.group(2)),
            "unit": "percent"
        }

    # single value: 99.5%
    match = re.search(r"(\d{2,3}\.\d+)%", value)
    if match:
        v = float(match.group(1))
        return {
            "min": v,
            "max": v,
            "unit": "percent"
        }

    return None