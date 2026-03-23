from fastapi import APIRouter, UploadFile, File
from app.services.document_service import process_document
import traceback

router = APIRouter()

@router.post("/")
async def upload_document(file: UploadFile = File(...)):
    try:
        print("🔥 Upload received:", file.filename)
        result = process_document(file)
        print("🔥 Upload received:", file.filename)
        return result

    except Exception as e:
        print("\n\n===== ERROR TRACEBACK =====")
        print(traceback.format_exc())
        print("===== END TRACEBACK =====\n\n")

        return {
            "error": str(e)
        }