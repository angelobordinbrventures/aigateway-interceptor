import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.types import JSON

from api.database.connection import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    user_identifier = Column(String(255), nullable=True, index=True)
    source_ip = Column(String(45), nullable=True)
    ai_provider = Column(String(100), nullable=False, index=True)
    action_taken = Column(String(50), nullable=False, index=True)
    findings = Column(JSON, nullable=True)
    request_hash = Column(String(64), nullable=True)
    response_code = Column(Integer, nullable=True)
    processing_time_ms = Column(Float, nullable=True)


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    ai_targets = Column(JSON, nullable=True)
    finding_categories = Column(JSON, nullable=True)
    action = Column(String(50), nullable=False)
    priority = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class SensitivePattern(Base):
    __tablename__ = "sensitive_patterns"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), nullable=False)
    pattern = Column(Text, nullable=False)
    is_regex = Column(Boolean, default=False)
    severity = Column(String(50), default="medium")
    enabled = Column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
