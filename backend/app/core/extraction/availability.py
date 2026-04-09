import re


def _has_availability_context(text: str) -> bool:
    keywords = [
        "uptime",
        "availability",
        "service availability",
        "system availability",
        "platform availability",
        "sla",
    ]
    return any(k in text for k in keywords)


def _context_score(text: str) -> int:
    score = 0

    if "sla" in text:
        score += 2
    if "guarantee" in text or "guaranteed" in text:
        score += 2
    if "availability" in text:
        score += 1
    if "uptime" in text:
        score += 1

    return score


def _normalize_percentage(value: str):
    match = re.search(r"(\d{2,3}(?:\.\d+)?)", value)
    if not match:
        return None

    val = float(match.group(1))

    return {
        "min": val,
        "max": val,
        "unit": "percent"
    }


def extract_availability(pages):
    candidates = []

    pattern = r"(\d{2,3}(?:\.\d+)?\s?%|\d{2,3}(?:\.\d+)?\s?percent)"

    for p in pages:
        page_num = p["page"]
        sentences = p["text"].split("\n")

        for sentence in sentences:
            text = sentence.lower()

            if not _has_availability_context(text):
                continue

            matches = re.findall(pattern, text, re.IGNORECASE)

            for m in matches:
                normalized = _normalize_percentage(m)

                candidates.append({
                    "value": m,
                    "normalized": normalized,
                    "source_text": sentence,
                    "page": page_num,
                    "source_file": p.get("source_file", "unknown"),
                    "confidence": 0.9,
                    "context_score": _context_score(text)
                })

    return candidates if candidates else None