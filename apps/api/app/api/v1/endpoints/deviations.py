"""
ByggSjekk – Deviation endpoints.

GET   /cases/{case_id}/deviations              – list deviations for a case
GET   /cases/{case_id}/deviations/{dev_id}     – get single deviation
PATCH /cases/{case_id}/deviations/{dev_id}     – update status / architect note
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.property_case import Deviation, DeviationStatus, PropertyCase
from app.models.user import User
from app.schemas.deviation import DeviationRead, DeviationUpdate

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


async def _get_deviation_or_404(
    case_id: uuid.UUID,
    dev_id: uuid.UUID,
    db: AsyncSession,
) -> Deviation:
    result = await db.execute(
        select(Deviation)
        .options(selectinload(Deviation.rule_matches))
        .where(
            Deviation.id == dev_id,
            Deviation.case_id == case_id,
        )
    )
    dev = result.scalar_one_or_none()
    if dev is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deviation {dev_id} not found for case {case_id}.",
        )
    return dev


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[DeviationRead],
    summary="List deviations for a case",
)
async def list_deviations(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dev_status: Annotated[DeviationStatus | None, Query(alias="status")] = None,
) -> list[Deviation]:
    await _get_case_or_404(case_id, db)

    query = (
        select(Deviation)
        .options(selectinload(Deviation.rule_matches))
        .where(Deviation.case_id == case_id)
        .order_by(Deviation.severity.desc(), Deviation.created_at.desc())
    )
    if dev_status is not None:
        query = query.where(Deviation.status == dev_status)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/{dev_id}",
    response_model=DeviationRead,
    summary="Get a single deviation",
)
async def get_deviation(
    case_id: uuid.UUID,
    dev_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deviation:
    return await _get_deviation_or_404(case_id, dev_id, db)


@router.patch(
    "/{dev_id}",
    response_model=DeviationRead,
    summary="Update a deviation (architect note / status)",
)
async def update_deviation(
    case_id: uuid.UUID,
    dev_id: uuid.UUID,
    body: DeviationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deviation:
    # Only architects may update deviations
    if not current_user.is_architect:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Architect privileges required to update deviations.",
        )

    dev = await _get_deviation_or_404(case_id, dev_id, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dev, field, value)

    db.add(dev)
    await db.flush()
    await db.refresh(dev)
    return dev
