# core/evidence/evidence_builder.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class Evidence:
    evidence_id: str
    vendor_id: str
    document_id: str

    field: str
    value: Any
    normalized_value: Any

    source_text: str
    page: int
    span: Optional[str]

    confidence: float
    extraction_method: str

    created_at: str
    version: str

class EvidenceBuilder:

    VERSION = "v1"

    @staticmethod
    def build(
        vendor_id: str,
        document_id: str,
        field: str,
        value: Any,
        normalized_value: Any,
        source_text: str,
        page: int,
        confidence: float,
        extraction_method: str,
        span: Optional[str] = None
    ) -> Evidence:

        return Evidence(
            evidence_id=str(uuid.uuid4()),
            vendor_id=vendor_id,
            document_id=document_id,

            field=field,
            value=value,
            normalized_value=normalized_value,

            source_text=source_text,
            page=page,
            span=span,

            confidence=confidence,
            extraction_method=extraction_method,

            created_at=datetime.utcnow().isoformat(),
            version=EvidenceBuilder.VERSION
        )
    @staticmethod
    def build_batch(
        vendor_id: str,
        document_id: str,
        extracted_fields: list
    ) -> list:

        evidence_list = []

        for item in extracted_fields:
            ev = EvidenceBuilder.build(
                vendor_id=vendor_id,
                document_id=document_id,
                field=item["field"],
                value=item["value"],
                normalized_value=item.get("normalized_value"),
                source_text=item["source_text"],
                page=item["page"],
                confidence=item.get("confidence", 0.9),
                extraction_method=item.get("method", "regex"),
                span=item.get("span")
            )
            evidence_list.append(ev)

        return evidence_list