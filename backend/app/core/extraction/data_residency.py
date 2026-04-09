import re

def extract_data_residency(pages):
    candidates = []

    patterns = [
        r"(data.*(stored|hosted|located).*(EU|Europe|Germany|France|region))",
        r"(hosted in (EU|Europe|Germany|France))"
    ]

    for p in pages:
        page_num = p["page"]
        sentences = p["text"].split("\n")

        for sentence in sentences:
            sentence_lower = sentence.lower()

            if "data" in sentence_lower or "hosted" in sentence_lower:

                for pattern in patterns:
                    match = re.search(pattern, sentence, re.IGNORECASE)

                    if match:
                        candidates.append({
                            "value": match.group(),
                            "source_text": sentence,
                            "page": page_num,
                            "source_file": p.get("source_file", "unknown")
                        })

    return candidates if candidates else None