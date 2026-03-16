"""
Municipality request endpoints – Phase 7.
Trigger and track requests to municipality for document approval status.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.deps import get_db, get_current_user
from app.models.property_case import (
    MunicipalityRequest, PropertyCase, Property,
    RequestStatus,
)
from app.models.user import User

router = APIRouter()


class MunicipalityRequestCreate(BaseModel):
    request_type: str = "approval_status"  # approval_status | case_history
    request_method: str = "EMAIL"  # API | EMAIL


@router.get("", response_model=list[dict], tags=["Municipality"])
async def list_municipality_requests(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all municipality requests for a case."""
    result = await db.execute(
        select(MunicipalityRequest)
        .where(MunicipalityRequest.case_id == case_id)
        .order_by(MunicipalityRequest.created_at.desc())
    )
    requests = result.scalars().all()
    return [_serialize(r) for r in requests]


@router.post("", response_model=dict, tags=["Municipality"], status_code=201)
async def create_municipality_request(
    case_id: str,
    body: MunicipalityRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a municipality information request for a case.

    Uses MockKommuneAdapter in dev, FallbackEmailAdapter as fallback.
    Records the request and response in municipality_requests table.
    """
    # Verify case exists and load property
    case_result = await db.execute(
        select(PropertyCase).where(PropertyCase.id == case_id)
    )
    case = case_result.scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    property_result = await db.execute(
        select(Property).where(Property.id == case.property_id)
    )
    prop = property_result.scalar_one_or_none()
    if prop is None:
        raise HTTPException(status_code=400, detail="Case has no associated property")

    # Import municipality adapter (lazy import for testability)
    import sys as _sys
    _sys.path.extend(["/app/services", "/app"])

    try:
        from municipality_connectors.adapter import get_municipality_adapter
        adapter = get_municipality_adapter(prop.municipality or "", use_mock=True)
        response_data = await adapter.fetch_approval_status(
            gnr=prop.gnr or "",
            bnr=prop.bnr or "",
            municipality=prop.municipality or "",
            document_type=body.request_type,
        )
        method = "API" if "email" not in str(type(adapter).__name__).lower() else "EMAIL"
        status = RequestStatus.RECEIVED
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Municipality adapter failed: %s", exc)
        response_data = {"error": str(exc), "note": "Manuell henvendelse til kommunen anbefales."}
        method = body.request_method
        status = RequestStatus.FAILED

    # Persist request record
    muni_request = MunicipalityRequest(
        id=str(uuid.uuid4()),
        case_id=case_id,
        municipality=prop.municipality or "",
        request_type=body.request_type,
        request_method=method,
        status=status,
        request_payload={
            "gnr": prop.gnr,
            "bnr": prop.bnr,
            "municipality": prop.municipality,
            "request_type": body.request_type,
        },
        response_payload=response_data,
        sent_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc) if status == RequestStatus.RECEIVED else None,
    )
    db.add(muni_request)
    await db.commit()
    await db.refresh(muni_request)

    return _serialize(muni_request)


def _serialize(r: MunicipalityRequest) -> dict:
    return {
        "id": str(r.id),
        "case_id": str(r.case_id),
        "municipality": r.municipality,
        "request_type": r.request_type,
        "request_method": str(r.request_method.value) if hasattr(r.request_method, "value") else str(r.request_method),
        "status": str(r.status.value) if hasattr(r.status, "value") else str(r.status),
        "request_payload": r.request_payload,
        "response_payload": r.response_payload,
        "sent_at": r.sent_at.isoformat() if r.sent_at else None,
        "received_at": r.received_at.isoformat() if r.received_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
