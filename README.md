# AIGateway Interceptor

[![CI](https://github.com/your-org/aigateway-interceptor/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/aigateway-interceptor/actions/workflows/ci.yml)
[![Docker Build](https://github.com/your-org/aigateway-interceptor/actions/workflows/docker-build.yml/badge.svg)](https://github.com/your-org/aigateway-interceptor/actions/workflows/docker-build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A transparent proxy that intercepts traffic to AI provider APIs (OpenAI, Anthropic, Google AI, Cohere, Mistral) to detect, log, and prevent sensitive data leakage. Deploy on-premise to enforce data loss prevention (DLP) policies before any data leaves your network.

## Architecture

```
┌──────────┐       ┌──────────────────────────────────────────┐       ┌──────────────┐
│  Users   │       │          AIGateway Interceptor           │       │  AI Provider │
│  & Apps  ├──────►│  Nginx ──► mitmproxy ──► DLP Engine     ├──────►│     APIs     │
│          │       │             │                             │       │              │
│          │       │  Dashboard ◄── FastAPI ◄── PostgreSQL    │       │  OpenAI      │
│          │       │                            Redis          │       │  Anthropic   │
└──────────┘       └──────────────────────────────────────────┘       │  Google AI   │
                                                                      │  Cohere      │
                                                                      │  Mistral     │
                                                                      └──────────────┘
```

## Features

- **Transparent HTTPS Interception** -- Intercepts AI API traffic via mitmproxy with custom CA
- **DLP Detection** -- Detects CPF, CNPJ, credit cards, emails, phone numbers, API keys, JWT tokens, and more
- **Configurable Actions** -- Block, anonymize, or log-only based on policy rules
- **Policy Engine** -- Priority-based policy evaluation with category and provider targeting
- **Real-time Dashboard** -- React-based UI with live log streaming via WebSocket
- **Audit Logging** -- Complete audit trail stored in PostgreSQL with JSONB findings
- **REST API** -- Full management API with JWT authentication
- **On-Premise First** -- Runs entirely within your infrastructure; no data sent to third parties
- **Docker-based** -- Single `docker compose up` to run the full stack

## Quick Start

Get running in under 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/aigateway-interceptor.git
cd aigateway-interceptor

# 2. Run the setup script
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh

# 3. Open the dashboard
open http://localhost
# Login: admin / admin123

# 4. Configure your application to use the proxy
export https_proxy=http://localhost:8080

# 5. Make an AI API call and see it in the dashboard
curl -x http://localhost:8080 https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-your-key"
```

### Manual Setup

```bash
# Generate TLS certificates
chmod +x infrastructure/certs/generate-ca.sh
./infrastructure/certs/generate-ca.sh

# Copy and edit environment config
cp .env.example .env

# Start all services
docker compose up --build -d

# Install CA certificate on your machine (for trusted interception)
chmod +x scripts/install-ca-cert.sh
./scripts/install-ca-cert.sh
```

## Screenshots

<!-- TODO: Add screenshots of the dashboard -->

| Dashboard Overview | Audit Log Detail | Policy Management |
|---|---|---|
| *Coming soon* | *Coming soon* | *Coming soon* |

## Services

| Service    | Port  | Description                          |
|------------|-------|--------------------------------------|
| Nginx      | 80    | Unified gateway                      |
| mitmproxy  | 8080  | HTTPS interception proxy             |
| FastAPI    | 8000  | REST API backend                     |
| Dashboard  | 3000  | React web interface                  |
| PostgreSQL | 5432  | Primary database                     |
| Redis      | 6379  | Cache and real-time messaging        |

## Configuration

All configuration is via environment variables. See [.env.example](.env.example) for the full list.

| Variable              | Default                          | Description                        |
|-----------------------|----------------------------------|------------------------------------|
| `SECRET_KEY`          | `change-this-...`                | JWT signing key                    |
| `DATABASE_URL`        | `postgresql://...`               | PostgreSQL connection string       |
| `REDIS_URL`           | `redis://redis:6379`             | Redis connection string            |
| `DLP_MODE`            | `anonymize`                      | Action mode: anonymize/block/log_only |
| `LOG_LEVEL`           | `INFO`                           | Logging verbosity                  |
| `LOG_RETENTION_DAYS`  | `90`                             | Audit log retention period         |
| `CORS_ORIGINS`        | `http://localhost:3000,...`       | Allowed CORS origins               |
| `AI_PROVIDER_DOMAINS` | `api.openai.com,...`             | Domains to intercept               |

## Development

### Prerequisites

- Docker Engine 24.0+
- Docker Compose v2.20+
- Python 3.11+ (for local development)
- Node.js 20+ (for dashboard development)

### Running Tests

```bash
# Run all tests
chmod +x scripts/run-tests.sh
./scripts/run-tests.sh

# Run proxy tests only
docker compose exec proxy pytest tests/ -v

# Run API tests only
docker compose exec api pytest tests/ -v
```

### Project Structure

```
aigateway-interceptor/
├── proxy/                   # mitmproxy-based interception proxy
│   ├── dlp/                 # DLP detection and anonymization
│   ├── policies/            # Policy engine
│   └── tests/               # Proxy unit tests
├── api/                     # FastAPI REST backend
│   ├── routers/             # API route handlers
│   ├── database/            # SQLAlchemy models and connection
│   ├── models/              # Pydantic schemas
│   └── tests/               # API unit tests
├── dashboard/               # React + Vite frontend
│   └── src/                 # React source code
├── infrastructure/
│   ├── postgres/            # Database init scripts
│   ├── nginx/               # Nginx configuration
│   └── certs/               # TLS certificate generation
├── scripts/                 # Setup and utility scripts
├── tests/
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── docs/                    # Documentation
│   └── decisions/           # Architecture Decision Records
├── docker-compose.yml       # Development stack
├── docker-compose.prod.yml  # Production overrides
└── .github/workflows/       # CI/CD pipelines
```

### Linting

```bash
# Install ruff
pip install ruff

# Lint
ruff check proxy/ api/

# Format
ruff format proxy/ api/
```

## Deployment

- **On-Premise:** See [docs/deployment-onpremise.md](docs/deployment-onpremise.md)
- **VPN Mode:** See [docs/deployment-vpn.md](docs/deployment-vpn.md) (planned)

### Production Deployment

```bash
# Use the production compose override
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [On-Premise Deployment](docs/deployment-onpremise.md)
- [ADR: Proxy Technology](docs/decisions/001-proxy-technology.md)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run the test suite: `./scripts/run-tests.sh`
5. Commit with a descriptive message
6. Push and open a Pull Request

Please follow these guidelines:
- Write tests for all new functionality
- Use `ruff` for linting and formatting
- Keep commits focused and atomic
- Update documentation for user-facing changes
- Never commit secrets, credentials, or PII

## License

MIT License

Copyright (c) 2026 AIGateway Interceptor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
