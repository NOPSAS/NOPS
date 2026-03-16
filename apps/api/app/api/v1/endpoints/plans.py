"""
Plan endpoints – returns StructuredPlan data for a case.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user
from app.models.property_case import StructuredPlan, SourceDocument, Space
from app.models.user import User

router = APIRouter()


@router.get("", response_model=list[dict], tags=["Plans"])
async def list_plans(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all structured plans for a case (one per processed document)."""
    result = await db.execute(
        select(StructuredPlan)
        .where(StructuredPlan.case_id == case_id)
        .order_by(StructuredPlan.created_at.desc())
    )
    plans = result.scalars().all()

    output = []
    for plan in plans:
        # Load spaces
        spaces_result = await db.execute(
            select(Space).where(Space.plan_id == str(plan.id))
        )
        spaces = spaces_result.scalars().all()

        # Load document info
        doc_result = await db.execute(
            select(SourceDocument).where(SourceDocument.id == plan.document_id)
        )
        doc = doc_result.scalar_one_or_none()

        output.append({
            "id": str(plan.id),
            "document_id": str(plan.document_id),
            "case_id": str(plan.case_id),
            "document_filename": doc.original_filename if doc else None,
            "document_type": doc.document_type if doc else None,
            "approval_status": str(doc.approval_status.value) if doc and doc.approval_status else None,
            "total_area": plan.total_area,
            "room_count": plan.room_count,
            "version": plan.version,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "spaces": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "space_type": s.space_type,
                    "floor_number": s.floor_number,
                    "area": s.area,
                    "confidence": s.confidence,
                    "attributes": s.attributes or {},
                }
                for s in spaces
            ],
            "plan_data": plan.plan_data,
        })
    return output


@router.get("/{plan_id}", response_model=dict, tags=["Plans"])
async def get_plan(
    case_id: str,
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific structured plan with all spaces."""
    result = await db.execute(
        select(StructuredPlan).where(
            StructuredPlan.id == plan_id,
            StructuredPlan.case_id == case_id,
        )
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    spaces_result = await db.execute(
        select(Space).where(Space.plan_id == plan_id)
    )
    spaces = spaces_result.scalars().all()

    doc_result = await db.execute(
        select(SourceDocument).where(SourceDocument.id == plan.document_id)
    )
    doc = doc_result.scalar_one_or_none()

    return {
        "id": str(plan.id),
        "document_id": str(plan.document_id),
        "case_id": str(plan.case_id),
        "document_filename": doc.original_filename if doc else None,
        "document_type": doc.document_type if doc else None,
        "approval_status": str(doc.approval_status.value) if doc and doc.approval_status else None,
        "total_area": plan.total_area,
        "room_count": plan.room_count,
        "version": plan.version,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "spaces": [
            {
                "id": str(s.id),
                "name": s.name,
                "space_type": s.space_type,
                "floor_number": s.floor_number,
                "area": s.area,
                "confidence": s.confidence,
                "attributes": s.attributes or {},
            }
            for s in spaces
        ],
        "plan_data": plan.plan_data,
    }
