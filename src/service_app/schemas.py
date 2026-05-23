"""Pydantic models for validated LLM parse output and API payloads."""

from pydantic import BaseModel, Field


class PartLine(BaseModel):
    name: str = Field(min_length=1)
    quantity: float = Field(gt=0)


class ParsedServiceCall(BaseModel):
    customer_name: str = Field(min_length=1)
    parts: list[PartLine] = Field(default_factory=list)
    labor_hours: float = Field(ge=0)


class ParseRequest(BaseModel):
    transcript: str = Field(min_length=1, description="Technician field note or job log line.")


class PricedPartLine(BaseModel):
    name: str
    quantity: float
    unit_price: float
    line_total: float


class ParseResponse(BaseModel):
    customer_name: str
    parts: list[PricedPartLine]
    labor_hours: float
    labor_rate: float
    labor_total: float
    parts_total: float
    estimated_total: float
