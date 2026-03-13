import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.connection import get_db
from api.database.models import AuditLog
from api.models.schemas import (
    AuditLogCreate,
    AuditLogResponse,
    PaginatedResponse,
)

router = APIRouter(prefix="/logs", tags=["logs"])


def _apply_filters(
    stmt,
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    user: Optional[str],
    ai_provider: Optional[str],
    action: Optional[str],
):
    if date_from is not None:
        stmt = stmt.where(AuditLog.timestamp >= date_from)
    if date_to is not None:
        stmt = stmt.where(AuditLog.timestamp <= date_to)
    if user is not None:
        stmt = stmt.where(AuditLog.user_identifier == user)
    if ai_provider is not None:
        stmt = stmt.where(AuditLog.ai_provider == ai_provider)
    if action is not None:
        stmt = stmt.where(AuditLog.action_taken == action)
    return stmt


@router.get("/export")
async def export_logs(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    user: Optional[str] = None,
    ai_provider: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())
    stmt = _apply_filters(stmt, date_from, date_to, user, ai_provider, action)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "timestamp", "user_identifier", "source_ip",
        "ai_provider", "action_taken", "findings", "request_hash",
        "response_code", "processing_time_ms",
    ])
    for log in logs:
        writer.writerow([
            str(log.id), log.timestamp.isoformat() if log.timestamp else "", log.user_identifier,
            log.source_ip, log.ai_provider, log.action_taken,
            str(log.findings) if log.findings else "",
            log.request_hash, log.response_code, log.processing_time_ms,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    user: Optional[str] = None,
    ai_provider: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count(AuditLog.id))
    count_stmt = _apply_filters(count_stmt, date_from, date_to, user, ai_provider, action)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(page_size)
    stmt = _apply_filters(stmt, date_from, date_to, user, ai_provider, action)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return PaginatedResponse(
        items=[AuditLogResponse.model_validate(log) for log in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return AuditLogResponse.model_validate(log)


@router.post("", response_model=AuditLogResponse, status_code=201)
async def create_log(
    payload: AuditLogCreate,
    db: AsyncSession = Depends(get_db),
):
    log = AuditLog(**payload.model_dump())
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return AuditLogResponse.model_validate(log)
