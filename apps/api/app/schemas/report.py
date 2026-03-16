"""
ByggSjekk – Assessment report and architect review schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.property_case import ReportType, ReviewStatus


# ---------------------------------------------------------------------------
# AssessmentReport
# ---------------------------------------------------------------------------


class AssessmentReportCreate(BaseModel):
    report_type: ReportType = ReportType.INTERNAL
    content: dict[str, Any] = Field(default_factory=dict)


class AssessmentReportGenerateRequest(BaseModel):
    """Request body for generating a new report from case deviations."""

    report_type: ReportType = ReportType.INTERNAL
    include_dismissed: bool = False


class AssessmentReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    report_type: ReportType
    content: dict[str, Any]
    approved_by_id: uuid.UUID | None
    approved_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# ArchitectReview
# ---------------------------------------------------------------------------


class ArchitectReviewCreate(BaseModel):
    comments: str | None = None
    overrides: dict[str, Any] | None = None


class ArchitectReviewUpdate(BaseModel):
    status: ReviewStatus | None = None
    comments: str | None = None
    overrides: dict[str, Any] | None = None


class ArchitectReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    reviewer_id: uuid.UUID
    status: ReviewStatus
    comments: str | None
    overrides: dict[str, Any] | None
    audit_log: list[Any] | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
