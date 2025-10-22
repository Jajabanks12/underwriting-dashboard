from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal


class Loss(BaseModel):
    date: Optional[str] = None
    paid: Optional[float] = 0.0
    reserve: Optional[float] = 0.0


class Address(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None


class Applicant(BaseModel):
    applicant_id: str = Field(default="TEMP")
    entity_type: Literal["individual", "business"] = "individual"
    age: Optional[int] = None
    years_in_business: Optional[int] = None
    naics: Optional[str] = None
    revenue_usd: Optional[float] = None
    loss_runs_36mo: List[Loss] = Field(default_factory=list)
    address: Address = Address()
    location_zone: Optional[str] = None
    prior_carrier: Optional[str] = None
    requested_limits: dict = Field(default_factory=dict)

    @field_validator("age")
    @classmethod
    def _clamp_age(cls, v):
        if v is None:
            return v
        return max(0, min(120, int(v)))
