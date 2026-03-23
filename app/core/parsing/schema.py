from pydantic import BaseModel, Field, validator
from typing import List, Optional


class Counterparty(BaseModel):
    name: str
    lei: Optional[str] = None
    country: str


class Exposure(BaseModel):
    amount: float
    currency: str
    exposure_type: str
    risk_weight: Optional[float] = None


class RegulatoryReport(BaseModel):
    report_id: str
    bank_id: str
    reporting_date: str

    counterparty: Counterparty
    exposures: List[Exposure]

    @validator("reporting_date")
    def validate_date(cls, v):
        # simple guard (extend later)
        if len(v) != 10:
            raise ValueError("Invalid date format (expected YYYY-MM-DD)")
        return v