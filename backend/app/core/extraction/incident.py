import re


DURATION_PATTERN = re.compile(
    r"\b("
    r"\d+\s*-\s*\d+\s*(?:min|mins|minute|minutes|hr|hrs|hour|hours|h)"
    r"|"
    r"\d+\s*(?:min|mins|minute|minutes|hr|hrs|hour|hours|h)"
    r")\b",
    re.IGNORECASE,
)

INCIDENT_CONTEXT_TERMS = [
    "incident",
    "security incident",
    "security event",
    "breach",
    "notification",
    "notify",
    "notified",
    "report",
    "reported",
    "reporting",
    "escalate",
    "escalation",
    "response",
]

TIME_QUALIFIER_TERMS = [
    "within",
    "no later than",
    "within the following",
    "must notify",
    "must report",
    "shall notify",
    "shall report",
    "upon discovery",
    "after discovery",
    "from detection",
    "from identification",
]


def _normalize_duration_to_minutes(raw_value):
    if not raw_value:
        return None

    # harden against non-string input
    if not isinstance(raw_value, str):
        raw_value = str(raw_value)

    text = raw_value.lower().strip()
    text = re.sub(r"\s+", " ", text)

    range_match = re.match(
        r"(\d+)\s*-\s*(\d+)\s*(min|mins|minute|minutes|hr|hrs|hour|hours|h)\b",
        text,
        re.IGNORECASE,
    )
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        unit = range_match.group(3).lower()

        if unit in {"hr", "hrs", "hour", "hours", "h"}:
            start *= 60
            end *= 60

        return {
            "min": start,
            "max": end,
            "unit": "minutes",
        }

    single_match = re.match(
        r"(\d+)\s*(min|mins|minute|minutes|hr|hrs|hour|hours|h)\b",
        text,
        re.IGNORECASE,
    )
    if single_match:
        value = int(single_match.group(1))
        unit = single_match.group(2).lower()

        if unit in {"hr", "hrs", "hour", "hours", "h"}:
            value *= 60

        return {
            "min": value,
            "max": value,
            "unit": "minutes",
        }

    return None


def _has_incident_context(sentence):
    s = sentence.lower()
    return any(term in s for term in INCIDENT_CONTEXT_TERMS)


def _has_time_qualifier(sentence):
    s = sentence.lower()
    return any(term in s for term in TIME_QUALIFIER_TERMS)


def _context_score(sentence):
    s = sentence.lower()
    score = 0

    if "incident" in s or "security incident" in s:
        score += 3
    if "breach" in s or "security event" in s:
        score += 2
    if "notify" in s or "notification" in s or "report" in s:
        score += 3
    if "within" in s or "no later than" in s:
        score += 2
    if "response" in s:
        score += 1

    return score


def extract_incident_time(pages):
    candidates = []

    for p in pages:
        page_num = p.get("page")
        source_file = p.get("source_file", "unknown")
        text = p.get("text", "")

        sentences = [line.strip() for line in text.split("\n") if line.strip()]

        for sentence in sentences:
            if not _has_incident_context(sentence):
                continue

            # use finditer instead of findall to guarantee string extraction
            matches = list(DURATION_PATTERN.finditer(sentence))
            if not matches:
                continue

            for match in matches:
                raw_value = match.group(0)
                normalized = _normalize_duration_to_minutes(raw_value)

                candidate = {
                    "value": raw_value,
                    "normalized": normalized,
                    "source_text": sentence,
                    "page": page_num,
                    "source_file": source_file,
                    "context_score": _context_score(sentence),
                    "has_time_qualifier": _has_time_qualifier(sentence),
                }

                candidates.append(candidate)

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: (
            x.get("context_score", 0),
            x.get("has_time_qualifier", False),
        ),
        reverse=True,
    )

    return candidates