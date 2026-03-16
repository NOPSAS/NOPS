"""
ByggSjekk – Document, evidence and plan schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.property_case import (
    ApprovalStatus,
    ProcessingStatus,
    SourceType,
)


# ---------------------------------------------------------------------------
# SourceDocument
# ---------------------------------------------------------------------------


class SourceDocumentCreate(BaseModel):
    """Internal schema used when persisting a newly uploaded document."""

    case_id: uuid.UUID
    filename: str = Field(max_length=512)
    original_filename: str = Field(max_length=512)
    storage_key: str = Field(max_length=1024)
    file_size: int = Field(ge=0)
    mime_type: str = Field(max_length=128)
    source_type: SourceType = SourceType.UPLOADED
    checksum: str = Field(max_length=64)
    metadata_: dict[str, Any] | None = None


class SourceDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    filename: str
    original_filename: str
    storage_key: str
    file_size: int
    mime_type: str
    source_type: SourceType
    approval_status: ApprovalStatus
    approval_status_confidence: float | None
    document_type: str | None
    document_type_confidence: float | None
    checksum: str
    processing_status: ProcessingStatus
    processing_error: str | None
    metadata_: dict[str, Any] | None = Field(alias="metadata_", default=None)
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# DocumentEvidence
# ---------------------------------------------------------------------------


class DocumentEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int | None
    bounding_box: dict[str, Any] | None
    text_excerpt: str | None
    observation: str
    confidence: float
    created_at: datetime


# ---------------------------------------------------------------------------
# StructuredPlan
# ---------------------------------------------------------------------------


class SpaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    name: str
    space_type: str
    floor_number: int | None
    area: float | None
    confidence: float
    attributes: dict[str, Any] | None
    created_at: datetime


class StructuredPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    case_id: uuid.UUID
    floor_number: int | None
    plan_data: dict[str, Any]
    total_area: float | None
    room_count: int | None
    version: int
    created_at: datetime
    updated_at: datetime

    spaces: list[SpaceRead] = Field(default_factory=list)
