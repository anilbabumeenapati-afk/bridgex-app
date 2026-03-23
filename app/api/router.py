from fastapi import APIRouter
from app.api.v1.endpoints import upload
from app.api.v1.endpoints import review
from fastapi import APIRouter
from app.db.session import SessionLocal
from app.db.models import EvidenceRecord
from app.api.v1.endpoints import evidence

api_router = APIRouter()
router = APIRouter()


api_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])

@router.get("/{record_id}")
def get_evidence(record_id: int):
    db = SessionLocal()
    record = db.query(EvidenceRecord).filter(EvidenceRecord.id == record_id).first()
    db.close()

    return record
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(review.router, prefix="/review", tags=["Review"])