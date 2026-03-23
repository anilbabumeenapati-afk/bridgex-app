from app.db.session import SessionLocal
from app.db.models import EvidenceRecord
from app.db.models import AuditLog
from datetime import datetime
from app.db.models import EvidenceVersion


def get_record(record_id):
    db = SessionLocal()
    record = db.query(EvidenceRecord).filter(
        EvidenceRecord.id == record_id
    ).first()
    db.close()
    return record

def save_evidence(evidence, validation):
    db = SessionLocal()
    try:
        record = EvidenceRecord(
            evidence=evidence,
            validation=validation,
            status="PENDING"
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.id
    finally:
        db.close()

def update_record(record_id, evidence):
    db = SessionLocal()

    record = db.query(EvidenceRecord).filter(
        EvidenceRecord.id == record_id
    ).first()

    if record:
        record.evidence = evidence
        db.commit()

    db.close()
    return record

def log_audit(record_id, field_name, action, old_value, new_value):
    db = SessionLocal()

    log = AuditLog(
        record_id=record_id,
        field_name=field_name,
        action=action,
        old_value=old_value,
        new_value=new_value,
        timestamp=datetime.utcnow()
    )

    db.add(log)
    db.commit()
    db.close()

def save_version(record_id: int, evidence: dict, validation: dict):
    db = SessionLocal()

    version = EvidenceVersion(
        record_id=record_id,
        evidence=evidence,
        validation=validation
    )

    db.add(version)
    db.commit()
    db.refresh(version)
    db.close()

    return {
        "version_id": version.id,
        "record_id": record_id
    }