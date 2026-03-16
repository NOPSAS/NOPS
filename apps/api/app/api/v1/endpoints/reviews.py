"""
ByggSjekk – Review and report endpoints.

GET  /cases/{case_id}/review          – get architect review
POST /cases/{case_id}/review          – create review
PATCH /cases/{case_id}/review         – update review
GET  /cases/{case_id}/report          – get assessment report
POST /cases/{case_id}/report/approve  – approve a report
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_architect, get_current_user, get_db
from app.models.property_case import (
    ArchitectReview,
    AssessmentReport,
    PropertyCase,
    ReportType,
    ReviewStatus,
)
from app.models.user import User
from app.schemas.report import (
    ArchitectReviewCreate,
    ArchitectReviewRead,
    ArchitectReviewUpdate,
    AssessmentReportCreate,
    AssessmentReportRead,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_case_or_404(case_id: uuid.UUID, db: AsyncSession) -> PropertyCase:
    case = await db.get(PropertyCase, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found.",
        )
    return case


async def _get_review_or_404(
    case_id: uuid.UUID, db: AsyncSession
) -> ArchitectReview:
    result = await db.execute(
        select(ArchitectReview)
        .where(ArchitectReview.case_id == case_id)
        .order_by(ArchitectReview.created_at.desc())
        .limit(1)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No review found for case {case_id}.",
        )
    return review


async def _get_latest_report_or_404(
    case_id: uuid.UUID, db: AsyncSession
) -> AssessmentReport:
    result = await db.execute(
        select(AssessmentReport)
        .where(AssessmentReport.case_id == case_id)
        .order_by(AssessmentReport.version.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No report found for case {case_id}.",
        )
    return report


# ---------------------------------------------------------------------------
# Review endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/review",
    response_model=ArchitectReviewRead,
    summary="Get the latest architect review for a case",
)
async def get_review(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArchitectReview:
    await _get_case_or_404(case_id, db)
    return await _get_review_or_404(case_id, db)


@router.post(
    "/review",
    response_model=ArchitectReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an architect review for a case",
)
async def create_review(
    case_id: uuid.UUID,
    body: ArchitectReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_architect),
) -> ArchitectReview:
    await _get_case_or_404(case_id, db)

    review = ArchitectReview(
        case_id=case_id,
        reviewer_id=current_user.id,
        status=ReviewStatus.PENDING,
        comments=body.comments,
        overrides=body.overrides or {},
        audit_log=[],
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)
    return review


@router.patch(
    "/review",
    response_model=ArchitectReviewRead,
    summary="Update the latest architect review",
)
async def update_review(
    case_id: uuid.UUID,
    body: ArchitectReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_architect),
) -> ArchitectReview:
    await _get_case_or_404(case_id, db)
    review = await _get_review_or_404(case_id, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    if body.status == ReviewStatus.COMPLETED and review.completed_at is None:
        review.completed_at = datetime.now(tz=timezone.utc)

    # Append audit log entry
    audit_log = list(review.audit_log or [])
    audit_log.append(
        {
            "actor_id": str(current_user.id),
            "action": "update",
            "changes": update_data,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
    )
    review.audit_log = audit_log

    db.add(review)
    await db.flush()
    await db.refresh(review)
    return review


# ---------------------------------------------------------------------------
# Report endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/report",
    response_model=AssessmentReportRead,
    summary="Get the latest assessment report for a case",
)
async def get_report(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssessmentReport:
    await _get_case_or_404(case_id, db)
    return await _get_latest_report_or_404(case_id, db)


@router.post(
    "/report",
    response_model=AssessmentReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assessment report for a case",
)
async def create_report(
    case_id: uuid.UUID,
    body: AssessmentReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_architect),
) -> AssessmentReport:
    await _get_case_or_404(case_id, db)

    # Determine next version number
    existing = await db.execute(
        select(AssessmentReport)
        .where(AssessmentReport.case_id == case_id)
        .order_by(AssessmentReport.version.desc())
        .limit(1)
    )
    latest = existing.scalar_one_or_none()
    next_version = (latest.version + 1) if latest else 1

    report = AssessmentReport(
        case_id=case_id,
        report_type=body.report_type,
        content=body.content,
        version=next_version,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


@router.post(
    "/report/generate",
    response_model=AssessmentReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new assessment report for a case (AI-assisted)",
)
async def generate_report(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_architect),
) -> AssessmentReport:
    """
    Genererer en ny vurderingsrapport ved hjelp av avviksmotoren og regelbasen.
    Returnerer INTERNAL-rapport med confidence-score og norsk begrunnelse.
    """
    from sqlalchemy import and_
    from app.models.property_case import Deviation, Rule, RuleMatch

    case = await _get_case_or_404(case_id, db)

    # Load deviations for this case
    dev_result = await db.execute(
        select(Deviation).where(Deviation.case_id == case_id)
    )
    deviations = dev_result.scalars().all()

    # Build report content in Norwegian
    deviation_summaries = []
    for dev in deviations:
        deviation_summaries.append({
            "kategori": dev.category.value if hasattr(dev.category, "value") else str(dev.category),
            "alvorlighet": dev.severity.value if hasattr(dev.severity, "value") else str(dev.severity),
            "beskrivelse": dev.description,
            "confidence": dev.confidence,
            "status": dev.status.value if hasattr(dev.status, "value") else str(dev.status),
        })

    # Determine next version
    existing = await db.execute(
        select(AssessmentReport)
        .where(AssessmentReport.case_id == case_id)
        .order_by(AssessmentReport.version.desc())
        .limit(1)
    )
    latest_existing = existing.scalar_one_or_none()
    next_version = (latest_existing.version + 1) if latest_existing else 1

    # Generate report content
    avg_confidence = (
        sum(d.confidence for d in deviations) / len(deviations)
        if deviations else 0.0
    )
    critical_count = sum(
        1 for d in deviations
        if (d.severity.value if hasattr(d.severity, "value") else str(d.severity)) in ("CRITICAL", "HIGH")
    )

    content = {
        "tittel": f"Avviksvurdering – {case.title}",
        "generert_av": "ByggSjekk AI-motor",
        "total_avvik": len(deviations),
        "kritiske_avvik": critical_count,
        "gjennomsnittlig_confidence": round(avg_confidence, 3),
        "avvik": deviation_summaries,
        "fraskrivelse": (
            "Denne rapporten er generert som beslutningsstøtte for ansvarlig arkitekt. "
            "Alle vurderinger er basert på AI-analyse og indikerer potensielle avvik – "
            "ikke juridiske konklusjoner. Arkitekten er alltid siste kontrollinstans."
        ),
        "versjon": next_version,
    }

    report = AssessmentReport(
        case_id=case_id,
        report_type=ReportType.INTERNAL,
        content=content,
        version=next_version,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


@router.post(
    "/report/approve",
    response_model=AssessmentReportRead,
    summary="Approve the latest assessment report",
)
async def approve_report(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_architect),
) -> AssessmentReport:
    await _get_case_or_404(case_id, db)
    report = await _get_latest_report_or_404(case_id, db)

    if report.approved_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report is already approved.",
        )

    report.approved_by_id = current_user.id
    report.approved_at = datetime.now(tz=timezone.utc)

    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report
