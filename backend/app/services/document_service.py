from io import BytesIO
from fastapi import UploadFile

from app.core.parsing.pdf_parser import extract_text_from_pdf
from app.services.extraction_service import extract_fields


def process_document(file: UploadFile):
    print("1. process_document start")
    contents = file.file.read()
    print("1. process_document start")
    file_obj = BytesIO(contents)
    print("2. file read complete")

    pages = extract_text_from_pdf(file_obj)

    for page in pages:
        page["source_file"] = file.filename

    extracted = extract_fields(
        pages=pages,
        source_file=file.filename,
    )
    return extracted