# AIGateway Interceptor - Architecture

## System Overview

The AIGateway Interceptor is a transparent proxy that sits between users and AI provider APIs. It inspects, logs, and optionally modifies traffic to enforce data loss prevention (DLP) policies before sensitive data reaches external AI services.

## Architecture Diagram

```
                                  AIGateway Interceptor
 ┌─────────┐         ┌──────────────────────────────────────────────────┐
 │         │         │                                                  │
 │  User   │         │  ┌─────────┐    ┌─────────────────────────────┐ │         ┌──────────────┐
 │ Browser ├────────►│  │  Nginx  ├───►│  React Dashboard (Port 80)  │ │         │              │
 │         │  HTTP   │  │ Gateway │    └─────────────────────────────┘ │         │   OpenAI     │
 └─────────┘  :80    │  │ (Port   │    ┌─────────────────────────────┐ │         │   Anthropic  │
              ───────►│  │  80)    ├───►│  FastAPI Backend (Port 8000)│ │         │   Google AI  │
                      │  └─────────┘    └──────────┬──────────────────┘ │         │   Cohere     │
                      │                            │                    │         │   Mistral    │
 ┌─────────┐         │  ┌─────────────────────────┐│                    │         │              │
 │  User   │         │  │                         ││                    │         └──────┬───────┘
 │ Desktop ├────────►│  │  mitmproxy (Port 8080)  ││                    │                │
 │  App    │  HTTPS  │  │  ┌───────────────────┐  ││                    │                │
 │         │  Proxy  │  │  │  DLP Detector     │  │├───┐                │                │
 └─────────┘  :8080  │  │  │  - Pattern Match  │  ││   │                │                │
              ───────►│  │  │  - Anonymizer     │  ││   │                │                │
                      │  │  │  - Policy Engine  │  ││   │                │                │
                      │  │  └───────────────────┘  ││   │                │         ┌──────┴───────┐
                      │  │           │              ││   │                ├────────►│  AI Provider │
                      │  │           │  Intercept,  ││   │                │  HTTPS  │     APIs     │
                      │  │           │  inspect,    ││   │                │         └──────────────┘
                      │  │           │  forward     ││   │                │
                      │  └───────────┼──────────────┘│   │                │
                      │              │               │   │                │
                      │         ┌────▼────┐    ┌─────▼───▼──┐            │
                      │         │  Redis  │    │ PostgreSQL │            │
                      │         │ (Cache) │    │  (Audit +  │            │
                      │         │  :6379  │    │  Policies) │            │
                      │         └─────────┘    │   :5432    │            │
                      │                        └────────────┘            │
                      │                                                  │
                      └──────────────────────────────────────────────────┘
```

## Component Descriptions

### 1. mitmproxy (Transparent Proxy)

**Role:** Intercepts HTTPS traffic between users and AI providers.

- Listens on port 8080 as an HTTP(S) proxy
- Uses a custom CA certificate to perform TLS interception
- Routes traffic through the DLP pipeline before forwarding
- Supports all major AI provider APIs

**Key modules:**
- `dlp/detector.py` - Pattern-based sensitive data detection (CPF, CNPJ, credit cards, API keys, etc.)
- `dlp/anonymizer.py` - Replaces detected sensitive data with masked values
- `policies/engine.py` - Evaluates policies to determine action (BLOCK, ANONYMIZE, LOG_ONLY)

### 2. FastAPI Backend (REST API)

**Role:** Provides the management and query API for the dashboard and external integrations.

- Audit log queries with filtering and pagination
- Policy CRUD operations
- User authentication (JWT-based)
- Real-time WebSocket endpoint for live log streaming
- Health and metrics endpoints

### 3. React Dashboard (Web UI)

**Role:** Visual interface for security teams to monitor and configure the interceptor.

- Real-time audit log viewer
- Policy management interface
- Analytics and charts (findings over time, top categories)
- User management

### 4. PostgreSQL

**Role:** Primary persistent storage.

- Audit logs with JSONB for flexible findings storage
- Policy definitions
- Sensitive pattern definitions
- User accounts

### 5. Redis

**Role:** Caching and real-time messaging.

- Caches frequently queried data (policy lookups, recent stats)
- Pub/sub channel for real-time WebSocket updates
- Rate limiting state

### 6. Nginx

**Role:** Reverse proxy and unified gateway.

- Routes `/api/` to FastAPI, `/` to dashboard
- WebSocket proxying for real-time features
- Rate limiting on API and login endpoints
- Security headers

## Data Flow

### Request Interception Flow

```
1. User application sends HTTPS request to AI provider
   (e.g., POST https://api.openai.com/v1/chat/completions)

2. Request is routed through mitmproxy (configured as HTTP proxy)

3. mitmproxy performs TLS interception using the custom CA certificate

4. DLP Detector scans the request body:
   a. Pattern matching (regex + literal) for sensitive data
   b. Each finding is categorized (cpf, credit_card, api_key, etc.)

5. Policy Engine evaluates findings against active policies:
   a. Policies are checked in priority order (highest first)
   b. First matching policy determines the action

6. Action is executed:
   - LOG_ONLY:  Request passes through unchanged, findings are logged
   - ANONYMIZE: Sensitive data is masked (e.g., "123.456.789-00" -> "***.***.***-**")
   - BLOCK:     Request is blocked with a 403 response

7. Audit log entry is written to PostgreSQL

8. Real-time event is published to Redis (for WebSocket subscribers)

9. If not blocked, the (possibly modified) request is forwarded to the AI provider

10. Response from AI provider is returned to the user
```

## Technology Stack Rationale

| Component   | Technology       | Rationale                                                                 |
|-------------|------------------|---------------------------------------------------------------------------|
| Proxy       | mitmproxy        | Mature, Python-based, scriptable, excellent TLS interception support      |
| API         | FastAPI          | High performance, async, automatic OpenAPI docs, Python ecosystem         |
| Dashboard   | React + Vite     | Fast development, rich ecosystem, TypeScript support                      |
| Database    | PostgreSQL       | JSONB for flexible log storage, robust, widely supported                  |
| Cache       | Redis            | Fast caching, pub/sub for real-time, rate limiting                        |
| Gateway     | Nginx            | Battle-tested reverse proxy, WebSocket support, rate limiting             |
| DLP         | Custom Python    | Full control over patterns, no external API dependencies                  |
| Auth        | JWT (PyJWT)      | Stateless, standard, works well with SPA frontends                        |
| Container   | Docker Compose   | Simple multi-service orchestration for dev and on-premise deployment      |

## Security Considerations

- The CA private key must be protected; compromise allows full traffic interception
- All inter-service communication happens on an isolated Docker network
- In production, only Nginx port 80/443 is exposed externally
- JWT tokens have configurable expiration
- Default admin password must be changed before production deployment
- Audit logs are immutable (append-only by design)
- Redis can be configured with authentication in production
