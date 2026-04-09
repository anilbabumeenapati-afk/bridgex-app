import pdfplumber

def extract_text_from_pdf(file):
    pages = []

    with pdfplumber.open(file) as pdf:
        for i, page in enumerate(pdf.pages):
            content = page.extract_text()
            if content:
                pages.append({
                    "page": i + 1,
                    "text": content
                })

    return pages