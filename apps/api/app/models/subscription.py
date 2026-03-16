"""
ByggSjekk – Subscription ORM model (Stripe).
"""
from __future__ import annotations
import uuid as _uuid
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin


class Subscription(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[_uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True, unique=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True, unique=True)
    plan: Mapped[str] = mapped_column(sa.String(32), nullable=False, default="FREE")
    # FREE, STARTER, PROFESSIONAL, ENTERPRISE
    status: Mapped[str] = mapped_column(sa.String(32), nullable=False, default="active")
    # active, canceled, past_due, trialing
    current_period_end: Mapped[sa.DateTime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())

    user: Mapped["User"] = relationship("User", back_populates="subscription", foreign_keys=[user_id])  # noqa

    def __repr__(self) -> str:
        return f"<Subscription user_id={self.user_id} plan={self.plan} status={self.status}>"
