"""
ByggSjekk – Deviation, rule and rule-match schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.property_case import (
    DeviationCategory,
    DeviationStatus,
    Severity,
)


# ---------------------------------------------------------------------------
# Rule
# ---------------------------------------------------------------------------


class RuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rule_code: str
    title: str
    description: str
    legal_reference: str
    source: str
    version: str
    applies_to_categories: list[str] | None
    parameters: dict[str, Any] | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# RuleMatch
# ---------------------------------------------------------------------------


class RuleMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    deviation_id: uuid.UUID
    rule_id: uuid.UUID
    rationale: str
    confidence: float
    match_type: str
    created_at: datetime

    rule: RuleRead | None = None


# ---------------------------------------------------------------------------
# Deviation
# ---------------------------------------------------------------------------


class DeviationCreate(BaseModel):
    case_id: uuid.UUID
    category: DeviationCategory
    severity: Severity
    description: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    evidence_ids: list[str] | None = None
    rule_ids: list[str] | None = None


class DeviationUpdate(BaseModel):
    """Fields that an architect can update on a deviation."""

    status: DeviationStatus | None = None
    architect_note: str | None = None
    severity: Severity | None = None


class DeviationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    category: DeviationCategory
    severity: Severity
    description: str
    confidence: float
    evidence_ids: list[str] | None
    rule_ids: list[str] | None
    status: DeviationStatus
    architect_note: str | None
    created_at: datetime
    updated_at: datetime

    rule_matches: list[RuleMatchRead] = Field(default_factory=list)
