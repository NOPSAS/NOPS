"""
ByggSjekk – ORM model registry.

Importing this package ensures all model classes are registered with the
SQLAlchemy declarative ``Base`` metadata – required before Alembic autogenerate
or ``Base.metadata.create_all()`` will see every table.
"""

from app.models.user import User  # noqa: F401
from app.models.property_case import (  # noqa: F401
    Property,
    PropertyCase,
    SourceDocument,
    DocumentEvidence,
    StructuredPlan,
    Space,
    Rule,
    Deviation,
    RuleMatch,
    AssessmentReport,
    ArchitectReview,
    DispensationCase,
    DispensationStatistics,
    MunicipalityRequest,
    # Enums – re-exported for convenience
    CaseStatus,
    CustomerType,
    SourceType,
    ApprovalStatus,
    ProcessingStatus,
    DeviationCategory,
    Severity,
    DeviationStatus,
    ReportType,
    ReviewStatus,
    RequestMethod,
    RequestStatus,
)

__all__ = [
    "User",
    "Property",
    "PropertyCase",
    "SourceDocument",
    "DocumentEvidence",
    "StructuredPlan",
    "Space",
    "Rule",
    "Deviation",
    "RuleMatch",
    "AssessmentReport",
    "ArchitectReview",
    "DispensationCase",
    "DispensationStatistics",
    "MunicipalityRequest",
    # Enums
    "CaseStatus",
    "CustomerType",
    "SourceType",
    "ApprovalStatus",
    "ProcessingStatus",
    "DeviationCategory",
    "Severity",
    "DeviationStatus",
    "ReportType",
    "ReviewStatus",
    "RequestMethod",
    "RequestStatus",
]
