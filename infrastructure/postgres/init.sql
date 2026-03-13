-- =============================================================================
-- AIGateway Interceptor - Database Initialization
-- =============================================================================
-- This script initializes the PostgreSQL database with all required tables,
-- indexes, and seed data for the AIGateway Interceptor system.
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Audit Logs table
-- Stores all interception events with findings and metadata
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_identifier VARCHAR(255),
    source_ip VARCHAR(45),
    ai_provider VARCHAR(100) NOT NULL,
    action_taken VARCHAR(50) NOT NULL,
    findings JSONB DEFAULT '[]',
    request_hash VARCHAR(64),
    response_code INTEGER,
    processing_time_ms INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- =============================================================================
-- Policies table
-- Defines interception rules: what to detect and how to respond
-- =============================================================================
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    ai_targets TEXT[],
    finding_categories TEXT[],
    action VARCHAR(50) NOT NULL DEFAULT 'LOG_ONLY',
    priority INTEGER DEFAULT 100,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Sensitive Patterns table
-- Custom regex and literal patterns for DLP detection
-- =============================================================================
CREATE TABLE IF NOT EXISTS sensitive_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    pattern TEXT NOT NULL,
    is_regex BOOLEAN DEFAULT TRUE,
    severity VARCHAR(20) DEFAULT 'HIGH',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Users table
-- Dashboard and API authentication
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Indexes for query performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_identifier);
CREATE INDEX IF NOT EXISTS idx_audit_logs_provider ON audit_logs(ai_provider);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action_taken);
CREATE INDEX IF NOT EXISTS idx_policies_priority ON policies(priority DESC);
CREATE INDEX IF NOT EXISTS idx_policies_enabled ON policies(enabled);

-- =============================================================================
-- Seed Data: Default Policies
-- =============================================================================
INSERT INTO policies (name, description, finding_categories, action, priority) VALUES
('Block Credentials', 'Block any request containing API keys or passwords', ARRAY['api_key', 'password', 'jwt_token'], 'BLOCK', 100),
('Block Financial Data', 'Block credit card numbers', ARRAY['credit_card'], 'BLOCK', 90),
('Anonymize PII', 'Anonymize personal identifiable information', ARRAY['cpf', 'cnpj', 'email', 'phone', 'rg'], 'ANONYMIZE', 80),
('Log Everything', 'Default logging policy', NULL, 'LOG_ONLY', 1);

-- =============================================================================
-- Seed Data: Default Admin User
-- Password: admin123 - CHANGE IN PRODUCTION
-- =============================================================================
INSERT INTO users (username, email, hashed_password, role) VALUES
('admin', 'admin@aigateway.local', '$2b$12$dtyN0w6U8F.MOQgtZGODPugg84LZWh0KtKJFHNWf8kmMUlZ9yDq5W', 'admin');
