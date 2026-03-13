# AIGateway Interceptor - API Reference

**Base URL:** `http://localhost:8000` (direct) or `http://localhost/api` (via gateway)

All endpoints return JSON. Authentication is via JWT Bearer token unless noted otherwise.

---

## Authentication

### POST /auth/login

Authenticate and receive a JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Response (401):**
```json
{
  "detail": "Invalid credentials"
}
```

### POST /auth/refresh

Refresh an existing JWT token.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Health

### GET /health

Health check endpoint. No authentication required.

**Response (200):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

---

## Audit Logs

### GET /logs

List audit log entries with pagination and filtering.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**

| Parameter        | Type     | Default | Description                              |
|------------------|----------|---------|------------------------------------------|
| `page`           | integer  | 1       | Page number                              |
| `per_page`       | integer  | 50      | Items per page (max 200)                 |
| `ai_provider`    | string   | -       | Filter by AI provider                    |
| `action_taken`   | string   | -       | Filter by action (BLOCK, ANONYMIZE, LOG_ONLY) |
| `user_identifier`| string   | -       | Filter by user                           |
| `date_from`      | datetime | -       | Start of date range (ISO 8601)           |
| `date_to`        | datetime | -       | End of date range (ISO 8601)             |
| `search`         | string   | -       | Full-text search in findings             |

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2026-03-13T10:30:00Z",
      "user_identifier": "john.doe",
      "source_ip": "192.168.1.100",
      "ai_provider": "openai",
      "action_taken": "ANONYMIZE",
      "findings": [
        {
          "category": "cpf",
          "value_preview": "123.456.***-**",
          "position": {"start": 45, "end": 59}
        }
      ],
      "request_hash": "a1b2c3d4...",
      "response_code": 200,
      "processing_time_ms": 12,
      "metadata": {}
    }
  ],
  "total": 1523,
  "page": 1,
  "per_page": 50,
  "pages": 31
}
```

### GET /logs/{id}

Get a single audit log entry by ID.

**Response (200):** Single audit log object (same schema as list items).

**Response (404):**
```json
{
  "detail": "Log entry not found"
}
```

### GET /logs/stats

Get aggregated statistics for the dashboard.

**Query Parameters:**

| Parameter   | Type     | Default    | Description                    |
|-------------|----------|------------|--------------------------------|
| `period`    | string   | `24h`      | Time period: 1h, 24h, 7d, 30d |

**Response (200):**
```json
{
  "total_requests": 15230,
  "blocked": 142,
  "anonymized": 3891,
  "logged_only": 11197,
  "top_categories": [
    {"category": "email", "count": 2341},
    {"category": "cpf", "count": 1890},
    {"category": "credit_card", "count": 142}
  ],
  "top_providers": [
    {"provider": "openai", "count": 8921},
    {"provider": "anthropic", "count": 4102}
  ],
  "timeline": [
    {"timestamp": "2026-03-13T00:00:00Z", "count": 523},
    {"timestamp": "2026-03-13T01:00:00Z", "count": 489}
  ]
}
```

---

## Policies

### GET /policies

List all policies.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Block Credentials",
      "description": "Block any request containing API keys or passwords",
      "ai_targets": null,
      "finding_categories": ["api_key", "password", "jwt_token"],
      "action": "BLOCK",
      "priority": 100,
      "enabled": true,
      "created_at": "2026-03-13T00:00:00Z",
      "updated_at": "2026-03-13T00:00:00Z"
    }
  ]
}
```

### POST /policies

Create a new policy.

**Headers:** `Authorization: Bearer <token>` (admin role required)

**Request:**
```json
{
  "name": "Block SSN",
  "description": "Block requests containing Social Security Numbers",
  "ai_targets": ["openai", "anthropic"],
  "finding_categories": ["ssn"],
  "action": "BLOCK",
  "priority": 95,
  "enabled": true
}
```

**Response (201):** Created policy object.

### PUT /policies/{id}

Update an existing policy.

**Headers:** `Authorization: Bearer <token>` (admin role required)

**Request:** Same schema as POST (all fields optional).

**Response (200):** Updated policy object.

### DELETE /policies/{id}

Delete a policy.

**Headers:** `Authorization: Bearer <token>` (admin role required)

**Response (204):** No content.

---

## Sensitive Patterns

### GET /patterns

List all sensitive data patterns.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Brazilian CPF",
      "category": "cpf",
      "pattern": "\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}",
      "is_regex": true,
      "severity": "HIGH",
      "enabled": true,
      "created_at": "2026-03-13T00:00:00Z"
    }
  ]
}
```

### POST /patterns

Create a new pattern.

**Headers:** `Authorization: Bearer <token>` (admin role required)

**Request:**
```json
{
  "name": "Custom Internal ID",
  "category": "internal_id",
  "pattern": "INT-\\d{8}",
  "is_regex": true,
  "severity": "MEDIUM",
  "enabled": true
}
```

**Response (201):** Created pattern object.

### PUT /patterns/{id}

Update a pattern.

### DELETE /patterns/{id}

Delete a pattern.

---

## Users

### GET /users

List all users (admin only).

**Headers:** `Authorization: Bearer <token>` (admin role required)

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "admin",
      "email": "admin@aigateway.local",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-03-13T00:00:00Z"
    }
  ]
}
```

### POST /users

Create a new user (admin only).

**Request:**
```json
{
  "username": "analyst1",
  "email": "analyst@company.com",
  "password": "securepassword123",
  "role": "viewer"
}
```

**Roles:** `admin`, `editor`, `viewer`

### PUT /users/{id}

Update a user.

### DELETE /users/{id}

Deactivate a user (soft delete).

---

## WebSocket

### WS /ws

Real-time audit log streaming.

**Authentication:** Pass JWT as query parameter: `/ws?token=<jwt>`

**Messages (server to client):**
```json
{
  "type": "new_log",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-03-13T10:30:00Z",
    "ai_provider": "openai",
    "action_taken": "ANONYMIZE",
    "findings_count": 2
  }
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning                                    |
|-------------|--------------------------------------------|
| 400         | Bad request (invalid parameters)           |
| 401         | Not authenticated                          |
| 403         | Insufficient permissions                   |
| 404         | Resource not found                         |
| 422         | Validation error (with field details)      |
| 429         | Rate limit exceeded                        |
| 500         | Internal server error                      |

## Rate Limits

- API endpoints: 30 requests/second per IP
- Login endpoint: 5 requests/minute per IP
- WebSocket: 1 connection per authenticated user
