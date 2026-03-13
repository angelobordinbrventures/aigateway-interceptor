from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.connection import get_db
from api.database.models import Policy
from api.models.schemas import (
    PaginatedResponse,
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
)

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=PaginatedResponse[PolicyResponse])
async def list_policies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(select(func.count(Policy.id)))
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Policy).order_by(Policy.priority.desc(), Policy.name).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return PaginatedResponse(
        items=[PolicyResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(
    payload: PolicyCreate,
    db: AsyncSession = Depends(get_db),
):
    policy = Policy(**payload.model_dump())
    db.add(policy)
    await db.flush()
    await db.refresh(policy)
    return PolicyResponse.model_validate(policy)


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return PolicyResponse.model_validate(policy)


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    payload: PolicyUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)

    await db.flush()
    await db.refresh(policy)
    return PolicyResponse.model_validate(policy)


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    await db.delete(policy)


@router.patch("/{policy_id}/toggle", response_model=PolicyResponse)
async def toggle_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy.enabled = not policy.enabled
    await db.flush()
    await db.refresh(policy)
    return PolicyResponse.model_validate(policy)
