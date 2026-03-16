"""
ByggSjekk / nops.no – Stripe fakturering og abonnement.

POST /billing/checkout          – opprett Stripe Checkout Session
POST /billing/portal            – opprett Stripe Customer Portal Session
POST /billing/webhook           – Stripe webhook handler
GET  /billing/subscription      – hent aktiv abonnementsinfo
"""
from __future__ import annotations

import logging
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.subscription import Subscription

router = APIRouter()
logger = logging.getLogger(__name__)

PLAN_LABELS = {
    "FREE": "Gratis",
    "STARTER": "Starter",
    "PROFESSIONAL": "Professional",
    "ENTERPRISE": "Enterprise",
}

PLAN_LIMITS = {
    "FREE": {"eiendomsoppslag": 5, "ai_analyser": 0, "pdf_rapporter": 0},
    "STARTER": {"eiendomsoppslag": 100, "ai_analyser": 20, "pdf_rapporter": 20},
    "PROFESSIONAL": {"eiendomsoppslag": -1, "ai_analyser": -1, "pdf_rapporter": -1},
    "ENTERPRISE": {"eiendomsoppslag": -1, "ai_analyser": -1, "pdf_rapporter": -1},
}


async def _hent_eller_opprett_subscription(user: User, db: AsyncSession) -> Subscription:
    result = await db.execute(select(Subscription).where(Subscription.user_id == str(user.id)))
    sub = result.scalar_one_or_none()
    if sub is None:
        sub = Subscription(user_id=str(user.id), plan="FREE", status="active")
        db.add(sub)
        await db.flush()
        await db.refresh(sub)
    return sub


@router.get("/subscription", summary="Hent abonnementsinfo")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    sub = await _hent_eller_opprett_subscription(current_user, db)
    return {
        "plan": sub.plan,
        "plan_label": PLAN_LABELS.get(sub.plan, sub.plan),
        "status": sub.status,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "limits": PLAN_LIMITS.get(sub.plan, PLAN_LIMITS["FREE"]),
        "has_stripe": bool(sub.stripe_subscription_id),
    }


@router.post("/checkout", summary="Opprett Stripe Checkout Session")
async def create_checkout(
    price_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    settings = get_settings()
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe er ikke konfigurert")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    sub = await _hent_eller_opprett_subscription(current_user, db)

    # Hent eller opprett Stripe customer
    customer_id = sub.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            name=current_user.full_name,
            metadata={"user_id": str(current_user.id)},
        )
        customer_id = customer.id
        sub.stripe_customer_id = customer_id
        await db.flush()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.NOPS_BASE_URL}/account/billing?success=1",
        cancel_url=f"{settings.NOPS_BASE_URL}/pricing",
        metadata={"user_id": str(current_user.id)},
    )
    return {"checkout_url": session.url}


@router.post("/portal", summary="Opprett Stripe Customer Portal Session")
async def create_portal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    settings = get_settings()
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe er ikke konfigurert")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    sub = await _hent_eller_opprett_subscription(current_user, db)

    if not sub.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Ingen aktiv Stripe-kunde funnet")

    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.NOPS_BASE_URL}/account/billing",
    )
    return {"portal_url": session.url}


@router.post("/webhook", summary="Stripe webhook handler", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    settings = get_settings()
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Ugyldig Stripe-signatur")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = data.get("metadata", {}).get("user_id")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")
        if user_id and subscription_id:
            result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
            sub = result.scalar_one_or_none()
            if sub:
                sub.stripe_subscription_id = subscription_id
                sub.stripe_customer_id = customer_id
                sub.status = "active"
                await db.flush()

    elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
        stripe_sub_id = data.get("id")
        new_status = data.get("status", "active")
        cancel_at_end = data.get("cancel_at_period_end", False)
        period_end_ts = data.get("current_period_end")
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = new_status
            sub.cancel_at_period_end = cancel_at_end
            if period_end_ts:
                import datetime
                sub.current_period_end = datetime.datetime.fromtimestamp(period_end_ts, tz=datetime.timezone.utc)
            # Bestem plan fra price_id
            items = data.get("items", {}).get("data", [])
            if items:
                price_id = items[0].get("price", {}).get("id", "")
                if price_id in (settings.STRIPE_PRICE_STARTER_MONTHLY, settings.STRIPE_PRICE_STARTER_YEARLY):
                    sub.plan = "STARTER"
                elif price_id in (settings.STRIPE_PRICE_PRO_MONTHLY, settings.STRIPE_PRICE_PRO_YEARLY):
                    sub.plan = "PROFESSIONAL"
            await db.flush()

    elif event_type == "customer.subscription.deleted":
        stripe_sub_id = data.get("id")
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = "canceled"
            sub.plan = "FREE"
            await db.flush()

    return {"received": True}
