"""Rules registry endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.models.property_case import Rule

router = APIRouter()


@router.get("/rules", response_model=list[dict], tags=["Rules"])
async def list_rules(
    source: str | None = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """List all rules, optionally filtered by source (TEK17, PBL, SAK10)."""
    stmt = select(Rule).where(Rule.is_active == is_active)
    if source:
        stmt = stmt.where(Rule.source == source.upper())
    stmt = stmt.order_by(Rule.source, Rule.rule_code)
    result = await db.execute(stmt)
    rules = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "rule_code": r.rule_code,
            "title": r.title,
            "description": r.description,
            "legal_reference": r.legal_reference,
            "source": r.source,
            "version": r.version,
            "applies_to_categories": r.applies_to_categories,
            "parameters": r.parameters,
            "is_active": r.is_active,
        }
        for r in rules
    ]


@router.get("/rules/{rule_code}", response_model=dict, tags=["Rules"])
async def get_rule(rule_code: str, db: AsyncSession = Depends(get_db)):
    """Get a specific rule by code."""
    result = await db.execute(select(Rule).where(Rule.rule_code == rule_code))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_code}' not found")
    return {
        "id": str(rule.id),
        "rule_code": rule.rule_code,
        "title": rule.title,
        "description": rule.description,
        "legal_reference": rule.legal_reference,
        "source": rule.source,
        "version": rule.version,
        "applies_to_categories": rule.applies_to_categories,
        "parameters": rule.parameters,
        "is_active": rule.is_active,
    }
