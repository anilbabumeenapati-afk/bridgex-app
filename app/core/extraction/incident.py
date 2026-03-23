import re

def extract_incident_time(pages):
    #sentences = text.split("\n")
    candidates = []

    pattern = r"(\d+\s?-\s?\d+\s?(?:min|minutes)|\d+\s?(?:min|minutes|hr|hour|hours))"

    for p in pages:
        page_num = p["page"]
        sentences = p["text"].split("\n")

    for sentence in sentences:
        if "incident" in sentence.lower() or "response" in sentence.lower():
            matches = re.findall(pattern, sentence, re.IGNORECASE)

            for m in matches:
                candidates.append({
                    "value": m,
                    "source_text": sentence
                })

    return candidates if candidates else None