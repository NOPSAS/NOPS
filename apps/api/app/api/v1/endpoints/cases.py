"""
ByggSjekk – PropertyCase CRUD endpoints.

GET    /cases              – paginated list (filter by status)
POST   /cases              – create a new case
GET    /cases/{case_id}    – fetch a single case
PATCH  /cases/{case_id}    – partial update
DELETE /cases/{case_id}    – soft-delete (set to ARCHIVED) or hard-delete
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.property_case import CaseStatus, Property, PropertyCase
from app.models.user import User
from app.schemas.case import (
    PaginatedPropertyCases,
    PropertyCaseCreate,
    PropertyCaseRead,
    PropertyCaseUpdate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_case_or_404(
    case_id: uuid.UUID,
    db: AsyncSession,
    current_user: User,
) -> PropertyCase:
    result = await db.execute(
        select(PropertyCase)
        .options(
            selectinload(PropertyCase.property),
            selectinload(PropertyCase.assigned_architect),
            selectinload(PropertyCase.created_by),
        )
        .where(PropertyCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found.",
        )
    return case


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PaginatedPropertyCases,
    summary="List property cases (paginated)",
)
async def list_cases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    case_status: Annotated[CaseStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedPropertyCases:
    query = select(PropertyCase).options(
        selectinload(PropertyCase.property),
    )

    # Non-architects only see their own cases
    if not current_user.is_architect:
        query = query.where(PropertyCase.created_by_id == current_user.id)

    if case_status is not None:
        query = query.where(PropertyCase.status == case_status)

    # Total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total: int = count_result.scalar_one()

    # Paginated rows
    query = (
        query.order_by(PropertyCase.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(query)).scalars().all()

    return PaginatedPropertyCases(
        total=total,
        page=page,
        page_size=page_size,
        items=[PropertyCaseRead.model_validate(r) for r in rows],
    )


@router.post(
    "",
    response_model=PropertyCaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new property case",
)
async def create_case(
    body: PropertyCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyCase:
    # Resolve property – either inline creation or reference to existing
    if body.property is not None:
        prop = Property(
            street_address=body.property.street_address,
            postal_code=body.property.postal_code,
            municipality=body.property.municipality,
            gnr=body.property.gnr,
            bnr=body.property.bnr,
            kommunenummer=body.property.kommunenummer,
            plan_references=body.property.plan_references or [],
        )
        db.add(prop)
        await db.flush()
    elif body.property_id is not None:
        prop = await db.get(Property, body.property_id)
        if prop is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Eiendom {body.property_id} ble ikke funnet.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enten 'property' (inline) eller 'property_id' må oppgis.",
        )

    # Auto-generate title from address if not provided
    title = body.title or f"{prop.street_address}, {prop.municipality}"

    case = PropertyCase(
        title=title,
        status=body.status,
        customer_type=body.customer_type,
        intake_source=body.intake_source,
        property_id=prop.id,
        created_by_id=current_user.id,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case, attribute_names=["property", "created_by"])
    return case


@router.get(
    "/{case_id}",
    response_model=PropertyCaseRead,
    summary="Fetch a single property case",
)
async def get_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyCase:
    return await _get_case_or_404(case_id, db, current_user)


@router.patch(
    "/{case_id}",
    response_model=PropertyCaseRead,
    summary="Partially update a property case",
)
async def update_case(
    case_id: uuid.UUID,
    body: PropertyCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyCase:
    case = await _get_case_or_404(case_id, db, current_user)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive (soft-delete) a property case",
    response_model=None,
)
async def delete_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    case = await _get_case_or_404(case_id, db, current_user)

    # Only architects or the case creator may delete
    if not current_user.is_architect and case.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this case.",
        )

    case.status = CaseStatus.ARCHIVED
    db.add(case)
