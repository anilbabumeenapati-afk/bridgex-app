from fastapi import APIRouter
from app.db.session import SessionLocal
from app.db.models import EvidenceRecord

from app.core.enrichment.metadata_enricher import enrich_evidence

# 🔥 IMPORT THIS
from app.api.v1.endpoints.review import normalize_for_ui


router = APIRouter()


@router.get("/{record_id}")
def get_evidence(record_id: int):
    db = SessionLocal()

    record = db.query(EvidenceRecord).filter(
        EvidenceRecord.id == record_id
    ).first()

    db.close()

    if not record:
        return {"error": "Not found"}

    evidence = record.evidence

    # -------------------------
    # 🔥 APPLY NORMALIZATION
    # -------------------------
    evidence = normalize_for_ui(evidence)

    # -------------------------
    # OPTIONAL: enrich (if needed)
    # -------------------------
    # evidence = enrich_evidence(evidence)

    return {
        "id": record.id,
        "evidence": evidence,
        "validation": record.validation,
        "status": record.status
    }