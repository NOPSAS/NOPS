"""
ByggSjekk – PropertyCase and Property schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.property_case import CaseStatus, CustomerType


# ---------------------------------------------------------------------------
# Property schemas
# ---------------------------------------------------------------------------


class PropertyCreate(BaseModel):
    street_address: str = Field(max_length=512)
    postal_code: str = Field(max_length=10)
    municipality: str = Field(max_length=256)
    gnr: int | None = None
    bnr: int | None = None
    kommunenummer: str | None = Field(default=None, max_length=10)
    plan_references: list[Any] | None = None


class PropertyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    street_address: str
    postal_code: str
    municipality: str
    gnr: int | None
    bnr: int | None
    kommunenummer: str | None = None
    plan_references: list[Any] | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# PropertyCase schemas
# ---------------------------------------------------------------------------


class PropertyCaseCreate(BaseModel):
    """
    Støtter to varianter:
    1. Inline-oppretting: send ``property`` med adressedata → oppretter Property automatisk
    2. Referanse til eksisterende: send ``property_id``
    """
    title: str | None = Field(default=None, max_length=512)
    status: CaseStatus = CaseStatus.DRAFT
    customer_type: CustomerType = CustomerType.PRIVATE
    intake_source: str | None = Field(default=None, max_length=256)
    property_id: uuid.UUID | None = None
    property: PropertyCreate | None = None


class PropertyCaseUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=512)
    status: CaseStatus | None = None
    customer_type: CustomerType | None = None
    intake_source: str | None = Field(default=None, max_length=256)
    assigned_architect_id: uuid.UUID | None = None


class PropertyCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: CaseStatus
    customer_type: CustomerType
    intake_source: str | None
    property_id: uuid.UUID
    assigned_architect_id: uuid.UUID | None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Nested reads – populated when the ORM loads the relationship
    property: PropertyRead | None = None


class PropertyCaseReadFull(PropertyCaseRead):
    """Extended read with all nested relationships loaded."""

    documents: list[Any] = Field(default_factory=list)
    deviations: list[Any] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Paginated list wrapper
# ---------------------------------------------------------------------------


class PaginatedPropertyCases(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PropertyCaseRead]
