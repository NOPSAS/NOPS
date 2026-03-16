"""
ByggSjekk – FastAPI dependency functions.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import verify_token
from app.db.base import AsyncSessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session, closing it when the request ends."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Authentication dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated User model or raise 401.

    Import is deferred inside the function to avoid circular imports at module
    load time.
    """
    from app.models.user import User  # local import – avoids circular deps

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return user


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated User if token is valid, else None. Never raises 401."""
    if not token:
        return None
    from app.models.user import User

    payload = verify_token(token)
    if payload is None:
        return None

    user_id: str | None = payload.get("sub")
    if user_id is None:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user and user.is_active:
        return user
    return None


async def get_current_active_architect(
    current_user=Depends(get_current_user),
):
    """Require that the authenticated user is an architect."""
    if not current_user.is_architect:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Architect privileges required",
        )
    return current_user


# ---------------------------------------------------------------------------
# Subscription / plan-gating dependencies
# ---------------------------------------------------------------------------

_AI_PLANS = {"FREE", "STARTER", "PROFESSIONAL", "ENTERPRISE"}
_PDF_PLANS = {"FREE", "STARTER", "PROFESSIONAL", "ENTERPRISE"}


async def _hent_plan(user, db: AsyncSession) -> str:
    """Return the user's current plan name, creating a FREE record if absent."""
    from app.models.subscription import Subscription  # local import

    result = await db.execute(select(Subscription).where(Subscription.user_id == str(user.id)))
    sub = result.scalar_one_or_none()
    if sub is None:
        sub = Subscription(user_id=str(user.id), plan="FREE", status="active")
        db.add(sub)
        await db.flush()
    return sub.plan


async def require_ai_access(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Require that the user has a plan that includes AI analysis."""
    plan = await _hent_plan(current_user, db)
    if plan not in _AI_PLANS:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "AI-analyse krever Starter-abonnement eller høyere. "
                "Oppgrader på /pricing."
            ),
        )
    return current_user


async def require_pdf_access(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Require that the user has a plan that includes PDF reports."""
    plan = await _hent_plan(current_user, db)
    if plan not in _PDF_PLANS:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "PDF-rapport krever Starter-abonnement eller høyere. "
                "Oppgrader på /pricing."
            ),
        )
    return current_user
