import re


def normalize_time(value: str):
    if not value:
        return None

    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)

    # -------------------------
    # RANGE: 10-20 min / 1-2 hours / 1 - 2 hr
    # -------------------------
    range_match = re.search(
        r"(\d+)\s*-\s*(\d+)\s*(min|mins|minute|minutes|hr|hrs|hour|hours|h)\b",
        value,
        re.IGNORECASE
    )
    if range_match:
        min_val = int(range_match.group(1))
        max_val = int(range_match.group(2))
        unit = range_match.group(3).lower()

        if unit in {"hr", "hrs", "hour", "hours", "h"}:
            min_val *= 60
            max_val *= 60

        return {
            "min": min_val,
            "max": max_val,
            "unit": "minutes"
        }

    # -------------------------
    # SINGLE: 30 min / 1 hour / 24h
    # -------------------------
    single_match = re.search(
        r"(\d+)\s*(min|mins|minute|minutes|hr|hrs|hour|hours|h)\b",
        value,
        re.IGNORECASE
    )
    if single_match:
        minutes = int(single_match.group(1))
        unit = single_match.group(2).lower()

        if unit in {"hr", "hrs", "hour", "hours", "h"}:
            minutes *= 60

        return {
            "min": minutes,
            "max": minutes,
            "unit": "minutes"
        }

    return None