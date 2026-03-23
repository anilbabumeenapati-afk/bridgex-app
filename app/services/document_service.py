from app.core.parsing.pdf_parser import extract_text_from_pdf
from app.services.extraction_service import extract_fields
from io import BytesIO

def process_document(file):
    contents = file.file.read()
    file_obj = BytesIO(contents)
    pages = extract_text_from_pdf(file_obj)

    # 🔥 FIX HERE
    text = "\n".join([p["text"] for p in pages])

    extracted = extract_fields(pages)
    return extracted