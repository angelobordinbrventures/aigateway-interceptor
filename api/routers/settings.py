from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from api.config import settings as app_settings
from api.database.connection import get_db
from api.database.models import SensitivePattern
from api.models.schemas import PatternCreate, PatternResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/retention")
async def get_retention():
    return {"retention_days": app_settings.LOG_RETENTION_DAYS}


@router.put("/retention")
async def update_retention(payload: dict):
    days = payload.get("retention_days", 90)
    app_settings.LOG_RETENTION_DAYS = int(days)
    return {"retention_days": app_settings.LOG_RETENTION_DAYS}


@router.get("/patterns", response_model=List[PatternResponse])
async def list_patterns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SensitivePattern).order_by(SensitivePattern.name))
    patterns = result.scalars().all()
    return [PatternResponse.model_validate(p) for p in patterns]


@router.post("/patterns", response_model=PatternResponse, status_code=201)
async def create_pattern(
    payload: PatternCreate,
    db: AsyncSession = Depends(get_db),
):
    pattern = SensitivePattern(
        name=payload.name,
        category=payload.category,
        pattern=payload.pattern,
        is_regex=payload.is_regex,
        severity=payload.severity,
        enabled=payload.enabled,
    )
    db.add(pattern)
    await db.flush()
    await db.refresh(pattern)
    return PatternResponse.model_validate(pattern)


@router.delete("/patterns/{pattern_id}")
async def delete_pattern(
    pattern_id: str,
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(pattern_id)
    result = await db.execute(select(SensitivePattern).where(SensitivePattern.id == pid))
    pattern = result.scalar_one_or_none()
    if pattern is None:
        raise HTTPException(status_code=404, detail="Pattern not found")
    await db.delete(pattern)
    return {"ok": True}
