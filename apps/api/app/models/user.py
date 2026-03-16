"""
ByggSjekk – User ORM model.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        sa.String(320),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    full_name: Mapped[str] = mapped_column(sa.String(512), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.true()
    )
    is_architect: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    email_verified: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    email_verification_token: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    password_reset_token: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)

    # Relationships (back-populated from PropertyCase)
    created_cases: Mapped[list["PropertyCase"]] = relationship(  # noqa: F821
        "PropertyCase",
        foreign_keys="PropertyCase.created_by_id",
        back_populates="created_by",
        lazy="select",
    )
    assigned_cases: Mapped[list["PropertyCase"]] = relationship(  # noqa: F821
        "PropertyCase",
        foreign_keys="PropertyCase.assigned_architect_id",
        back_populates="assigned_architect",
        lazy="select",
    )
    reviews: Mapped[list["ArchitectReview"]] = relationship(  # noqa: F821
        "ArchitectReview",
        foreign_keys="ArchitectReview.reviewer_id",
        back_populates="reviewer",
        lazy="select",
    )
    subscription: Mapped["Subscription | None"] = relationship(  # noqa: F821
        "Subscription",
        foreign_keys="Subscription.user_id",
        back_populates="user",
        uselist=False,
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
