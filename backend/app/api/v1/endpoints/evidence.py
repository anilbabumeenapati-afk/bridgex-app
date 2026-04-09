from fastapi import APIRouter
from app.db.session import SessionLocal
from app.db.models import EvidenceRecord
from app.core.enrichment.metadata_enricher import enrich_evidence
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
    evidence = enrich_evidence(evidence)
    evidence = normalize_for_ui(evidence)

    return {
        "id": record.id,
        "evidence": evidence,
        "validation": record.validation,
        "status": record.status,
        "state": evidence.get("state", {}),
        "vendor_profile": evidence.get("vendor_profile", {}),
    }