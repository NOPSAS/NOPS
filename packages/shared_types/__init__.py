# packages/shared_types – Delte Pydantic-modeller og enums
# Importeres av apps/api/ og kan generere TypeScript-typer via datamodel-code-generator.

from .models import (
    CaseStatus,
    CustomerType,
    ApprovalStatus,
    DeviationCategory,
    DeviationSeverity,
    DeviationStatus,
    ProcessingStatus,
    SourceType,
    ReportType,
)

__all__ = [
    "CaseStatus",
    "CustomerType",
    "ApprovalStatus",
    "DeviationCategory",
    "DeviationSeverity",
    "DeviationStatus",
    "ProcessingStatus",
    "SourceType",
    "ReportType",
]
