import uuid
from datetime import datetime
from typing import Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Policy schemas
# ---------------------------------------------------------------------------

class PolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    ai_targets: Optional[List[str]] = None
    finding_categories: Optional[List[str]] = None
    action: str = Field(..., min_length=1, max_length=50)
    priority: int = 0
    enabled: bool = True


class PolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    ai_targets: Optional[List[str]] = None
    finding_categories: Optional[List[str]] = None
    action: Optional[str] = Field(None, min_length=1, max_length=50)
    priority: Optional[int] = None
    enabled: Optional[bool] = None


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    ai_targets: Optional[List[str]] = None
    finding_categories: Optional[List[str]] = None
    action: str
    priority: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Audit log schemas
# ---------------------------------------------------------------------------

class AuditLogCreate(BaseModel):
    user_identifier: Optional[str] = None
    source_ip: Optional[str] = None
    ai_provider: str
    action_taken: str
    findings: Optional[Dict] = None
    request_hash: Optional[str] = None
    response_code: Optional[int] = None
    processing_time_ms: Optional[float] = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    user_identifier: Optional[str] = None
    source_ip: Optional[str] = None
    ai_provider: str
    action_taken: str
    findings: Optional[Dict] = None
    request_hash: Optional[str] = None
    response_code: Optional[int] = None
    processing_time_ms: Optional[float] = None


class AuditLogFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    user: Optional[str] = None
    ai_provider: Optional[str] = None
    action: Optional[str] = None


# ---------------------------------------------------------------------------
# Pattern schemas
# ---------------------------------------------------------------------------

class PatternCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str
    pattern: str
    is_regex: bool = False
    severity: str = "medium"
    enabled: bool = True


class PatternResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    pattern: str
    is_regex: bool
    severity: str
    enabled: bool


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    role: str = "viewer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Stats schemas
# ---------------------------------------------------------------------------

class StatsResponse(BaseModel):
    total_requests: int
    blocked: int
    anonymized: int
    allowed: int
    top_users: List[Dict]
    top_categories: List[Dict]


class TimelinePoint(BaseModel):
    hour: datetime
    total: int
    blocked: int
    anonymized: int
    allowed: int


class ProviderStat(BaseModel):
    provider: str
    total: int
    blocked: int
    anonymized: int
    allowed: int
