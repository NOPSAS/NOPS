"""
ByggSjekk – SQLAlchemy async database setup.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ---------------------------------------------------------------------------
# Database initialisation helper
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """Create all tables that are not yet present in the database.

    In production prefer Alembic migrations.  This function is useful for
    tests and first-time local setup.
    """
    # Import all models so SQLAlchemy registers their metadata before
    # calling create_all.
    import app.models  # noqa: F401 – side-effect import

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
