from datetime import datetime, timedelta, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.connection import get_db
from api.database.models import AuditLog
from api.models.schemas import ProviderStat, StatsResponse, TimelinePoint

router = APIRouter(prefix="/stats", tags=["stats"])


def _last_24h() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=24)


@router.get("/overview", response_model=StatsResponse)
async def stats_overview(db: AsyncSession = Depends(get_db)):
    since = _last_24h()

    total_q = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.timestamp >= since)
    )
    total = total_q.scalar_one()

    blocked_q = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= since, AuditLog.action_taken == "blocked"
        )
    )
    blocked = blocked_q.scalar_one()

    anonymized_q = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= since, AuditLog.action_taken == "anonymized"
        )
    )
    anonymized = anonymized_q.scalar_one()

    allowed_q = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= since, AuditLog.action_taken == "allowed"
        )
    )
    allowed = allowed_q.scalar_one()

    # Top users
    top_users_q = await db.execute(
        select(AuditLog.user_identifier, func.count(AuditLog.id).label("count"))
        .where(AuditLog.timestamp >= since, AuditLog.user_identifier.isnot(None))
        .group_by(AuditLog.user_identifier)
        .order_by(func.count(AuditLog.id).desc())
        .limit(5)
    )
    top_users = [{"user": row[0], "count": row[1]} for row in top_users_q.all()]

    top_categories: List[Dict] = []

    return StatsResponse(
        total_requests=total,
        blocked=blocked,
        anonymized=anonymized,
        allowed=allowed,
        top_users=top_users,
        top_categories=top_categories,
    )


@router.get("/timeline", response_model=List[TimelinePoint])
async def stats_timeline(db: AsyncSession = Depends(get_db)):
    """Hourly breakdown for the last 24 hours."""
    since = _last_24h()
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(AuditLog).where(AuditLog.timestamp >= since).order_by(AuditLog.timestamp)
    )
    logs = result.scalars().all()

    # Create 24 hourly buckets
    buckets: Dict[int, Dict] = {}
    for h in range(24):
        bucket_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=23 - h)
        buckets[h] = {
            "hour": bucket_time,
            "total": 0,
            "blocked": 0,
            "anonymized": 0,
            "allowed": 0,
        }

    for log in logs:
        ts = log.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        hours_ago = (now - ts).total_seconds() / 3600
        bucket_idx = 23 - min(int(hours_ago), 23)
        buckets[bucket_idx]["total"] += 1
        action = log.action_taken
        if action in ("blocked", "anonymized", "allowed"):
            buckets[bucket_idx][action] += 1

    return [TimelinePoint(**b) for b in buckets.values()]


@router.get("/top-users", response_model=List[Dict])
async def top_users(db: AsyncSession = Depends(get_db)):
    since = _last_24h()
    result = await db.execute(
        select(AuditLog.user_identifier, func.count(AuditLog.id).label("count"))
        .where(AuditLog.timestamp >= since, AuditLog.user_identifier.isnot(None))
        .group_by(AuditLog.user_identifier)
        .order_by(func.count(AuditLog.id).desc())
        .limit(5)
    )
    return [{"user": row[0], "count": row[1]} for row in result.all()]


@router.get("/top-categories", response_model=List[Dict])
async def top_categories(db: AsyncSession = Depends(get_db)):
    """Top 5 sensitive data categories from the last 24h."""
    return []


@router.get("/by-provider", response_model=List[ProviderStat])
async def stats_by_provider(db: AsyncSession = Depends(get_db)):
    since = _last_24h()
    result = await db.execute(
        select(
            AuditLog.ai_provider,
            func.count(AuditLog.id).label("total"),
            func.count(case((AuditLog.action_taken == "blocked", 1))).label("blocked"),
            func.count(case((AuditLog.action_taken == "anonymized", 1))).label("anonymized"),
            func.count(case((AuditLog.action_taken == "allowed", 1))).label("allowed"),
        )
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.ai_provider)
        .order_by(func.count(AuditLog.id).desc())
    )
    return [
        ProviderStat(
            provider=row[0],
            total=row[1],
            blocked=row[2],
            anonymized=row[3],
            allowed=row[4],
        )
        for row in result.all()
    ]
