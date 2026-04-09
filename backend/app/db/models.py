from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from app.db.session import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    record_id = Column(Integer)
    field_name = Column(String)

    action = Column(String)  # APPROVED / REJECTED / MODIFIED

    old_value = Column(JSON)
    new_value = Column(JSON)

    timestamp = Column(DateTime, default=datetime.utcnow)

class EvidenceRecord(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)

    # store full object
    evidence = Column(JSON)
    validation = Column(JSON)

    status = Column(String, default="PENDING")
    record_id = Column(Integer)
    version = Column(Integer)

class EvidenceVersion(Base):
    __tablename__ = "evidence_versions"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, index=True)

    evidence = Column(JSON)
    validation = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)