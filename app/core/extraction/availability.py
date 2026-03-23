import re

def extract_availability(pages):
    candidates = []

    for p in pages:
        page_num = p["page"]
        sentences = p["text"].split("\n")

        for sentence in sentences:
            if "uptime" in sentence.lower() or "availability" in sentence.lower():
                matches = re.findall(r"\d{2,3}\.\d+%", sentence)
                for m in matches:
                    candidates.append({
                        "value": m,
                        "source_text": sentence,
                        "page": page_num
                    })

    return candidates if candidates else None