import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import JSON, TypeDecorator

from api.database.connection import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# Use a type that works with both PostgreSQL (native UUID) and SQLite (string)
class FlexibleUUID(TypeDecorator):
    """UUID type that works with both PostgreSQL and SQLite."""

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(FlexibleUUID(), primary_key=True, default=_new_uuid)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, index=True)
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

    id = Column(FlexibleUUID(), primary_key=True, default=_new_uuid)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    ai_targets = Column(JSON, nullable=True)
    finding_categories = Column(JSON, nullable=True)
    action = Column(String(50), nullable=False)
    priority = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class SensitivePattern(Base):
    __tablename__ = "sensitive_patterns"

    id = Column(FlexibleUUID(), primary_key=True, default=_new_uuid)
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), nullable=False)
    pattern = Column(Text, nullable=False)
    is_regex = Column(Boolean, default=False)
    severity = Column(String(50), default="medium")
    enabled = Column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"

    id = Column(FlexibleUUID(), primary_key=True, default=_new_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
