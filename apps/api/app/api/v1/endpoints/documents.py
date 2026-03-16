"""
ByggSjekk – Document upload and management endpoints.

POST   /cases/{case_id}/documents           – multipart upload
GET    /cases/{case_id}/documents           – list documents for a case
GET    /cases/{case_id}/documents/{doc_id}  – get a single document
DELETE /cases/{case_id}/documents/{doc_id}  – delete document
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

import arq
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.property_case import ProcessingStatus, PropertyCase, SourceDocument, SourceType
from app.models.user import User
from app.schemas.document import SourceDocumentRead
from app.services.storage import get_storage_adapter

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_document_or_404(
    case_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession,
) -> SourceDocument:
    result = await db.execute(
        select(SourceDocument).where(
            SourceDocument.id == doc_id,
            SourceDocument.case_id == case_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found for case {case_id}.",
        )
    return doc


async def _get_case_or_404(case_id: uuid.UUID, db: AsyncSession) -> PropertyCase:
    case = await db.get(PropertyCase, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found.",
        )
    return case


async def _get_arq_pool() -> arq.ArqRedis:
    return await arq.create_pool(arq.connections.RedisSettings.from_dsn(settings.REDIS_URL))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SourceDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document to a case",
)
async def upload_document(
    case_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SourceDocument:
    await _get_case_or_404(case_id, db)

    content = await file.read()
    checksum = hashlib.sha256(content).hexdigest()
    file_size = len(content)

    # Derive a stable storage key
    storage_key = f"cases/{case_id}/documents/{checksum}/{file.filename}"
    mime_type = file.content_type or "application/octet-stream"

    # Persist to object storage
    storage = get_storage_adapter()
    await storage.upload(
        file=content,  # type: ignore[arg-type]
        key=storage_key,
        content_type=mime_type,
    )

    # Sanitise the stored filename
    safe_filename = f"{checksum[:8]}_{file.filename}"

    doc = SourceDocument(
        case_id=case_id,
        filename=safe_filename,
        original_filename=file.filename or "unknown",
        storage_key=storage_key,
        file_size=file_size,
        mime_type=mime_type,
        source_type=SourceType.UPLOADED,
        checksum=checksum,
        processing_status=ProcessingStatus.PENDING,
        metadata_={"uploaded_by": str(current_user.id)},
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    # Enqueue background processing job
    try:
        pool = await _get_arq_pool()
        await pool.enqueue_job("process_document", str(doc.id))
        await pool.aclose()
    except Exception:
        # Non-fatal: processing can be retried manually
        pass

    return doc


@router.get(
    "",
    response_model=list[SourceDocumentRead],
    summary="List documents for a case",
)
async def list_documents(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SourceDocument]:
    await _get_case_or_404(case_id, db)
    result = await db.execute(
        select(SourceDocument)
        .where(SourceDocument.case_id == case_id)
        .order_by(SourceDocument.created_at.desc())
    )
    return list(result.scalars().all())


@router.get(
    "/{doc_id}",
    response_model=SourceDocumentRead,
    summary="Get a single document",
)
async def get_document(
    case_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SourceDocument:
    return await _get_document_or_404(case_id, doc_id, db)


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
    response_model=None,
)
async def delete_document(
    case_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    doc = await _get_document_or_404(case_id, doc_id, db)

    # Remove from object storage (best-effort)
    try:
        storage = get_storage_adapter()
        await storage.delete(doc.storage_key)
    except Exception:
        pass

    await db.delete(doc)
