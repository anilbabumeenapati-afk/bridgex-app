# app/core/validation/gatekeeper.py

def gatekeep_document(pages: list):
    """
    Minimal gatekeeping:
    - Ensure document has extractable text
    - Prevent completely unusable input
    """

    # 1. Empty check
    if not pages or len(pages) == 0:
        return {
            "status": "FAIL",
            "reason": "Empty document"
        }

    # 2. Check if ANY page has meaningful text
    has_text = False

    for page in pages:
        if page and isinstance(page, str) and page.strip():
            has_text = True
            break

    if not has_text:
        return {
        "status": "WARN",
        "reason": "No extractable text found (possible OCR/scanned document)"
    }

    # 3. Soft signal check (optional but useful)
    combined_text = " ".join(pages).lower()

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