# app/core/validation/gatekeeper.py

def gatekeep_document(pages: list):
    """
    Minimal gatekeeping:
    - Ensure document has extractable text
    - Prevent completely unusable input
    - Works with parser output shaped like:
        [{"page": 1, "text": "..."}]
    """

    # 1. Empty check
    if not pages or len(pages) == 0:
        return {
            "status": "FAIL",
            "reason": "Empty document"
        }

    # 2. Collect extractable text from parsed pages
    text_chunks = []

    for page in pages:
        if isinstance(page, dict):
            text = page.get("text", "")
            if isinstance(text, str) and text.strip():
                text_chunks.append(text.strip())

        elif isinstance(page, str):
            # fallback for older calling style
            if page.strip():
                text_chunks.append(page.strip())

    if not text_chunks:
        return {
            "status": "WARN",
            "reason": "No extractable text found (possible OCR/scanned document)"
        }

    # 3. Soft signal check
    combined_text = " ".join(text_chunks).lower()

    keywords = ["uptime", "availability", "incident", "response"]

    found_signal = any(k in combined_text for k in keywords)

    if not found_signal:
        return {
            "status": "WARN",
            "reason": "No expected SLA keywords found"
        }

    return {
        "status": "PASS",
        "reason": "Document accepted"
    }