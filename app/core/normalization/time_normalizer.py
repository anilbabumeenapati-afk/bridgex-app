import re

def normalize_time(value: str):
    value = value.lower().strip()

    # convert hr → minutes
    if "hr" in value or "hour" in value:
        match = re.search(r"\d+", value)
        if match:
            minutes = int(match.group()) * 60
            return {
                "min": minutes,
                "max": minutes,
                "unit": "minutes"
            }

    # range: 10-20 min
    match = re.search(r"(\d+)\s*-\s*(\d+)\s*(min|minutes)", value)
    if match:
        return {
            "min": int(match.group(1)),
            "max": int(match.group(2)),
            "unit": "minutes"
        }

    # single minutes
    match = re.search(r"(\d+)\s*(min|minutes)", value)
    if match:
        m = int(match.group(1))
        return {
            "min": m,
            "max": m,
            "unit": "minutes"
        }

    return None