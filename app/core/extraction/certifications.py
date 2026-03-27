import re

def extract_certifications(pages):
    candidates = []

    patterns = [
        r"ISO[\s\-]?27001",
        r"SOC[\s\-]?2",
        r"PCI[\s\-]?DSS"
    ]

    for p in pages:
        page_num = p["page"]
        sentences = p["text"].split("\n")

        for sentence in sentences:
            for pattern in patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)

                if match:
                    candidates.append({
                        "value": match.group().upper().replace(" ", "").replace("-", ""),
                        "source_text": sentence,
                        "page": page_num
                    })

    return candidates if candidates else None