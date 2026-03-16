"""
ByggSjekk – Core domain ORM models.

All models are defined in a single file to keep the inter-model foreign-key
references simple and avoid circular imports.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# Python enum definitions (used by sa.Enum columns)
# ---------------------------------------------------------------------------


class CaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class CustomerType(str, enum.Enum):
    PRIVATE = "PRIVATE"
    PROFESSIONAL = "PROFESSIONAL"
    MUNICIPALITY = "MUNICIPALITY"


class SourceType(str, enum.Enum):
    UPLOADED = "UPLOADED"
    FETCHED_MUNICIPALITY = "FETCHED_MUNICIPALITY"
    EMAIL_REQUEST = "EMAIL_REQUEST"


class ApprovalStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    ASSUMED_APPROVED = "ASSUMED_APPROVED"
    VERIFIED_APPROVED = "VERIFIED_APPROVED"
    UNKNOWN = "UNKNOWN"


class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DeviationCategory(str, enum.Enum):
    ROOM_DEFINITION_CHANGE = "ROOM_DEFINITION_CHANGE"
    BEDROOM_UTILITY_DISCREPANCY = "BEDROOM_UTILITY_DISCREPANCY"
    DOOR_PLACEMENT_CHANGE = "DOOR_PLACEMENT_CHANGE"
    WINDOW_PLACEMENT_CHANGE = "WINDOW_PLACEMENT_CHANGE"
    BALCONY_TERRACE_DISCREPANCY = "BALCONY_TERRACE_DISCREPANCY"
    ADDITION_DETECTED = "ADDITION_DETECTED"
    UNDERBUILDING_DETECTED = "UNDERBUILDING_DETECTED"
    UNINSPECTED_AREA = "UNINSPECTED_AREA"
    USE_CHANGE_INDICATION = "USE_CHANGE_INDICATION"
    MARKETED_FUNCTION_DISCREPANCY = "MARKETED_FUNCTION_DISCREPANCY"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DeviationStatus(str, enum.Enum):
    OPEN = "OPEN"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"
    CONFIRMED = "CONFIRMED"


class ReportType(str, enum.Enum):
    INTERNAL = "INTERNAL"
    CUSTOMER = "CUSTOMER"


class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class RequestMethod(str, enum.Enum):
    API = "API"
    EMAIL = "EMAIL"


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    RECEIVED = "RECEIVED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------


class Property(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "properties"

    street_address: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    postal_code: Mapped[str] = mapped_column(sa.String(10), nullable=False)
    municipality: Mapped[str] = mapped_column(sa.String(256), nullable=False, index=True)
    gnr: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    bnr: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    kommunenummer: Mapped[str | None] = mapped_column(sa.String(10), nullable=True)
    plan_references: Mapped[list[Any] | None] = mapped_column(
        sa.JSON, nullable=True, default=list
    )

    # Relationships
    cases: Mapped[list["PropertyCase"]] = relationship(
        "PropertyCase", back_populates="property", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Property id={self.id} address={self.street_address!r}>"


# ---------------------------------------------------------------------------
# PropertyCase
# ---------------------------------------------------------------------------


class PropertyCase(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "property_cases"

    title: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        sa.Enum(CaseStatus, name="case_status"),
        nullable=False,
        default=CaseStatus.DRAFT,
        server_default=CaseStatus.DRAFT.value,
        index=True,
    )
    customer_type: Mapped[CustomerType] = mapped_column(
        sa.Enum(CustomerType, name="customer_type"),
        nullable=False,
        default=CustomerType.PRIVATE,
    )
    intake_source: Mapped[str | None] = mapped_column(sa.String(256), nullable=True)

    # FKs
    property_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("properties.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_architect_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Relationships
    property: Mapped["Property"] = relationship(
        "Property", back_populates="cases", lazy="joined"
    )
    assigned_architect: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_architect_id],
        back_populates="assigned_cases",
        lazy="joined",
    )
    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="created_cases",
        lazy="joined",
    )
    documents: Mapped[list["SourceDocument"]] = relationship(
        "SourceDocument", back_populates="case", lazy="select"
    )
    deviations: Mapped[list["Deviation"]] = relationship(
        "Deviation", back_populates="case", lazy="select"
    )
    reports: Mapped[list["AssessmentReport"]] = relationship(
        "AssessmentReport", back_populates="case", lazy="select"
    )
    reviews: Mapped[list["ArchitectReview"]] = relationship(
        "ArchitectReview", back_populates="case", lazy="select"
    )
    municipality_requests: Mapped[list["MunicipalityRequest"]] = relationship(
        "MunicipalityRequest", back_populates="case", lazy="select"
    )
    dispensation_cases: Mapped[list["DispensationCase"]] = relationship(
        "DispensationCase", back_populates="case", lazy="select"
    )
    structured_plans: Mapped[list["StructuredPlan"]] = relationship(
        "StructuredPlan", back_populates="case", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<PropertyCase id={self.id} title={self.title!r} status={self.status}>"


# ---------------------------------------------------------------------------
# SourceDocument
# ---------------------------------------------------------------------------


class SourceDocument(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "source_documents"

    case_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        sa.Enum(SourceType, name="source_type"),
        nullable=False,
        default=SourceType.UPLOADED,
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        sa.Enum(ApprovalStatus, name="approval_status"),
        nullable=False,
        default=ApprovalStatus.UNKNOWN,
    )
    approval_status_confidence: Mapped[float | None] = mapped_column(
        sa.Float, nullable=True
    )
    document_type: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    document_type_confidence: Mapped[float | None] = mapped_column(
        sa.Float, nullable=True
    )
    checksum: Mapped[str] = mapped_column(sa.String(64), nullable=False)  # sha256 hex
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        sa.Enum(ProcessingStatus, name="processing_status"),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True,
    )
    processing_error: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", sa.JSON, nullable=True, default=dict
    )

    # Relationships
    case: Mapped["PropertyCase"] = relationship(
        "PropertyCase", back_populates="documents"
    )
    evidence: Mapped[list["DocumentEvidence"]] = relationship(
        "DocumentEvidence", back_populates="document", lazy="select"
    )
    structured_plans: Mapped[list["StructuredPlan"]] = relationship(
        "StructuredPlan", back_populates="document", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<SourceDocument id={self.id} filename={self.original_filename!r} "
            f"status={self.processing_status}>"
        )


# ---------------------------------------------------------------------------
# DocumentEvidence
# ---------------------------------------------------------------------------


class DocumentEvidence(UUIDMixin, Base):
    __tablename__ = "document_evidence"

    document_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    bounding_box: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True
    )
    text_excerpt: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    observation: Mapped[str] = mapped_column(sa.Text, nullable=False)
    confidence: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["SourceDocument"] = relationship(
        "SourceDocument", back_populates="evidence"
    )

    def __repr__(self) -> str:
        return f"<DocumentEvidence id={self.id} doc={self.document_id}>"


# ---------------------------------------------------------------------------
# StructuredPlan
# ---------------------------------------------------------------------------


class StructuredPlan(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "structured_plans"

    document_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    floor_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    plan_data: Mapped[dict[str, Any]] = mapped_column(
        sa.JSON, nullable=False, default=dict
    )
    total_area: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    room_count: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    # Relationships
    document: Mapped["SourceDocument"] = relationship(
        "SourceDocument", back_populates="structured_plans"
    )
    case: Mapped["PropertyCase"] = relationship(
        "PropertyCase", back_populates="structured_plans"
    )
    spaces: Mapped[list["Space"]] = relationship(
        "Space", back_populates="plan", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<StructuredPlan id={self.id} case={self.case_id} "
            f"floor={self.floor_number} v{self.version}>"
        )


# ---------------------------------------------------------------------------
# Space
# ---------------------------------------------------------------------------


class Space(UUIDMixin, Base):
    __tablename__ = "spaces"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("structured_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    space_type: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    floor_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    area: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    confidence: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    # Relationships
    plan: Mapped["StructuredPlan"] = relationship(
        "StructuredPlan", back_populates="spaces"
    )

    def __repr__(self) -> str:
        return f"<Space id={self.id} name={self.name!r} type={self.space_type}>"


# ---------------------------------------------------------------------------
# Rule
# ---------------------------------------------------------------------------


class Rule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "rules"

    rule_code: Mapped[str] = mapped_column(
        sa.String(64), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    legal_reference: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    source: Mapped[str] = mapped_column(sa.String(64), nullable=False)  # TEK17/PBL/SAK10
    version: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    applies_to_categories: Mapped[list[str] | None] = mapped_column(
        sa.JSON, nullable=True, default=list
    )
    parameters: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True, default=dict
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.true()
    )

    # Relationships
    rule_matches: Mapped[list["RuleMatch"]] = relationship(
        "RuleMatch", back_populates="rule", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Rule code={self.rule_code!r} source={self.source}>"


# ---------------------------------------------------------------------------
# Deviation
# ---------------------------------------------------------------------------


class Deviation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "deviations"

    case_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[DeviationCategory] = mapped_column(
        sa.Enum(DeviationCategory, name="deviation_category"),
        nullable=False,
        index=True,
    )
    severity: Mapped[Severity] = mapped_column(
        sa.Enum(Severity, name="severity"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    confidence: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    evidence_ids: Mapped[list[str] | None] = mapped_column(
        sa.JSON, nullable=True, default=list
    )
    rule_ids: Mapped[list[str] | None] = mapped_column(
        sa.JSON, nullable=True, default=list
    )
    status: Mapped[DeviationStatus] = mapped_column(
        sa.Enum(DeviationStatus, name="deviation_status"),
        nullable=False,
        default=DeviationStatus.OPEN,
        index=True,
    )
    architect_note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Relationships
    case: Mapped["PropertyCase"] = relationship(
        "PropertyCase", back_populates="deviations"
    )
    rule_matches: Mapped[list["RuleMatch"]] = relationship(
        "RuleMatch", back_populates="deviation", lazy="select"
    )
    dispensation_cases: Mapped[list["DispensationCase"]] = relationship(
        "DispensationCase", back_populates="deviation", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<Deviation id={self.id} category={self.category} "
            f"severity={self.severity} status={self.status}>"
        )


# ---------------------------------------------------------------------------
# RuleMatch
# ---------------------------------------------------------------------------


class RuleMatch(UUIDMixin, Base):
    __tablename__ = "rule_matches"

    deviation_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("deviations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rationale: Mapped[str] = mapped_column(sa.Text, nullable=False)
    confidence: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    match_type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    # Relationships
    deviation: Mapped["Deviation"] = relationship(
        "Deviation", back_populates="rule_matches"
    )
    rule: Mapped["Rule"] = relationship("Rule", back_populates="rule_matches")

    def __repr__(self) -> str:
        return (
            f"<RuleMatch deviation={self.deviation_id} rule={self.rule_id} "
            f"confidence={self.confidence:.2f}>"
        )


# ---------------------------------------------------------------------------
# AssessmentReport
# ---------------------------------------------------------------------------


class AssessmentReport(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "assessment_reports"

    case_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_type: Mapped[ReportType] = mapped_column(
        sa.Enum(ReportType, name="report_type"),
        nullable=False,
        default=ReportType.INTERNAL,
    )
    content: Mapped[dict[str, Any]] = mapped_column(
        sa.JSON, nullable=False, default=dict
    )
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    # Relationships
    case: Mapped["PropertyCase"] = relationship(
        "PropertyCase", back_populates="reports"
    )
    approved_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[approved_by_id], lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<AssessmentReport id={self.id} case={self.case_id} "
            f"type={self.report_type} v{self.version}>"
        )


# ---------------------------------------------------------------------------
# ArchitectReview
# ---------------------------------------------------------------------------


class ArchitectReview(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "architect_reviews"

    case_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[ReviewStatus] = mapped_column(
        sa.Enum(ReviewStatus, name="review_status"),
        nullable=False,
        default=ReviewStatus.PENDING,
        index=True,
    )
    comments: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    overrides: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True, default=dict
    )
    audit_log: Mapped[list[Any] | None] = mapped_column(
        sa.JSON, nullable=True, default=list
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    # Relationships
    case: Mapped["PropertyCase"] = relationship(
        "PropertyCase", back_populates="reviews"
    )
    reviewer: Mapped["User"] = relationship(
        "User", foreign_keys=[reviewer_id], back_populates="reviews", lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<ArchitectReview id={self.id} case={self.case_id} "
            f"reviewer={self.reviewer_id} status={self.status}>"
        )


# ---------------------------------------------------------------------------
# DispensationCase
# ---------------------------------------------------------------------------


class DispensationCase(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "dispensation_cases"

    case_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deviation_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("deviations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(64), nullable=False, default="PENDING"
    )

    # Relationships
    case: Mapped["PropertyCase"] = relationship(
        "PropertyCase", back_populates="dispensation_cases"
    )
    deviation: Mapped["Deviation | None"] = relationship(
        "Deviation", back_populates="dispensation_cases", lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<DispensationCase id={self.id} case={self.case_id} "
            f"status={self.status}>"
        )


# ---------------------------------------------------------------------------
# DispensationStatistics
# ---------------------------------------------------------------------------


class DispensationStatistics(UUIDMixin, Base):
    __tablename__ = "dispensation_statistics"

    municipality: Mapped[str] = mapped_column(
        sa.String(256), nullable=False, index=True
    )
    rule_code: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    total_applications: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0
    )
    approved_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    rejected_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    year: Mapped[int] = mapped_column(sa.Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "municipality", "rule_code", "year", name="uq_dispensation_stats"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DispensationStatistics municipality={self.municipality!r} "
            f"rule={self.rule_code!r} year={self.year}>"
        )


# ---------------------------------------------------------------------------
# MunicipalityRequest
# ---------------------------------------------------------------------------


class MunicipalityRequest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "municipality_requests"

    case_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    municipality: Mapped[str] = mapped_column(
        sa.String(256), nullable=False, index=True
    )
    request_type: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    request_method: Mapped[RequestMethod] = mapped_column(
        sa.Enum(RequestMethod, name="request_method"),
        nullable=False,
        default=RequestMethod.EMAIL,
    )
    status: Mapped[RequestStatus] = mapped_column(
        sa.Enum(RequestStatus, name="request_status"),
        nullable=False,
        default=RequestStatus.PENDING,
        index=True,
    )
    request_payload: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True, default=dict
    )
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    received_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    # Relationships
    case: Mapped["PropertyCase"] = relationship(
        "PropertyCase", back_populates="municipality_requests"
    )

    def __repr__(self) -> str:
        return (
            f"<MunicipalityRequest id={self.id} case={self.case_id} "
            f"municipality={self.municipality!r} status={self.status}>"
        )
