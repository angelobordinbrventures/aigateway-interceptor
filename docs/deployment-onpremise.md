# AIGateway Interceptor - On-Premise Deployment Guide

## Prerequisites

### Hardware Requirements

| Component         | Minimum         | Recommended       |
|-------------------|-----------------|-------------------|
| CPU               | 2 cores         | 4+ cores          |
| RAM               | 4 GB            | 8+ GB             |
| Disk              | 20 GB           | 100+ GB (for logs)|
| Network           | 100 Mbps        | 1 Gbps            |

### Software Requirements

- Docker Engine 24.0+
- Docker Compose v2.20+
- OpenSSL 1.1+
- Git
- curl (for verification)

### Network Requirements

- Outbound HTTPS (443) to AI provider APIs
- Inbound access to port 80 (dashboard) and 8080 (proxy) from client machines
- Internal ports: 5432 (PostgreSQL), 6379 (Redis), 8000 (API) -- not exposed externally in production

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/aigateway-interceptor.git
cd aigateway-interceptor
```

### 2. Generate TLS Certificates

The proxy needs a Certificate Authority (CA) to intercept HTTPS traffic.

```bash
chmod +x infrastructure/certs/generate-ca.sh
./infrastructure/certs/generate-ca.sh
```

This creates:
- `infrastructure/certs/aigateway-ca.key` -- CA private key (keep secure)
- `infrastructure/certs/aigateway-ca.crt` -- CA certificate (distribute to clients)
- `infrastructure/certs/server.key` -- Server private key
- `infrastructure/certs/server.crt` -- Server certificate

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set production values:

```bash
# REQUIRED: Generate a strong secret key
SECRET_KEY=$(openssl rand -hex 32)

# REQUIRED: Set strong database password
POSTGRES_PASSWORD=your-strong-password-here
DATABASE_URL=postgresql://aigateway:your-strong-password-here@postgres:5432/aigateway

# Adjust DLP mode
DLP_MODE=anonymize  # or: block, log_only

# Set allowed CORS origins to your actual domain
CORS_ORIGINS=https://aigateway.yourcompany.com

# Set the dashboard API URL
VITE_API_URL=https://aigateway.yourcompany.com/api
```

### 4. Deploy the Stack

```bash
# Production deployment (only exposes ports 80/443)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 5. Verify Deployment

```bash
# Check all services are running
docker compose ps

# Check service health
curl http://localhost/health
curl http://localhost/api/health

# View logs
docker compose logs -f
```

### 6. Change Default Admin Password

Log in to the dashboard at `http://your-server/` with:
- Username: `admin`
- Password: `admin123`

Immediately change the password through the user settings.

## CA Certificate Installation

Every client machine that will route traffic through the proxy must trust the CA certificate.

### macOS

```bash
# Automated
chmod +x scripts/install-ca-cert.sh
./scripts/install-ca-cert.sh

# Manual
sudo security add-trusted-cert -d -r trustRoot \
    -k /Library/Keychains/System.keychain \
    infrastructure/certs/aigateway-ca.crt
```

**Browser-specific:**
- **Safari / Chrome:** Use the System Keychain automatically.
- **Firefox:** Settings > Privacy & Security > Certificates > View Certificates > Authorities > Import

### Ubuntu / Debian

```bash
sudo cp infrastructure/certs/aigateway-ca.crt /usr/local/share/ca-certificates/aigateway-ca.crt
sudo update-ca-certificates
```

### RHEL / CentOS / Fedora

```bash
sudo cp infrastructure/certs/aigateway-ca.crt /etc/pki/ca-trust/source/anchors/aigateway-ca.crt
sudo update-ca-trust extract
```

### Windows

1. Double-click `aigateway-ca.crt`
2. Click "Install Certificate"
3. Select "Local Machine"
4. Choose "Place all certificates in the following store"
5. Browse > "Trusted Root Certification Authorities"
6. Click Finish

**Or via PowerShell (Administrator):**
```powershell
Import-Certificate -FilePath "aigateway-ca.crt" -CertStoreLocation "Cert:\LocalMachine\Root"
```

### Mass Deployment (Active Directory)

For organizations using Active Directory, deploy the CA certificate via Group Policy:

1. Open Group Policy Management Console
2. Edit the appropriate GPO
3. Navigate to: Computer Configuration > Policies > Windows Settings > Security Settings > Public Key Policies > Trusted Root Certification Authorities
4. Right-click > Import > Select `aigateway-ca.crt`

## Client Proxy Configuration

### System-wide (Environment Variables)

```bash
export http_proxy=http://aigateway-server:8080
export https_proxy=http://aigateway-server:8080
export no_proxy=localhost,127.0.0.1,.yourcompany.com
```

### PAC File (Recommended for Enterprise)

Create a PAC file that routes only AI provider traffic through the proxy:

```javascript
function FindProxyForURL(url, host) {
    var aiProviders = [
        "api.openai.com",
        "api.anthropic.com",
        "generativelanguage.googleapis.com",
        "api.cohere.ai",
        "api.mistral.ai"
    ];

    for (var i = 0; i < aiProviders.length; i++) {
        if (dnsDomainIs(host, aiProviders[i])) {
            return "PROXY aigateway-server:8080";
        }
    }

    return "DIRECT";
}
```

## Configuration Options

### DLP Modes

| Mode        | Behavior                                             |
|-------------|------------------------------------------------------|
| `log_only`  | Logs findings but forwards request unchanged         |
| `anonymize` | Replaces sensitive data with masked values           |
| `block`     | Returns 403 and blocks the request entirely          |

### Policy Priority

Policies are evaluated in descending priority order. The first matching policy determines the action. A priority of 100 is evaluated before 90, which is evaluated before 1.

### Log Retention

Set `LOG_RETENTION_DAYS` to control how long audit logs are kept. A background job purges logs older than this threshold.

## Troubleshooting

### Services not starting

```bash
# Check individual service logs
docker compose logs proxy
docker compose logs api
docker compose logs postgres

# Restart a specific service
docker compose restart api
```

### Certificate not trusted

```bash
# Verify the CA cert is installed
openssl verify -CAfile infrastructure/certs/aigateway-ca.crt infrastructure/certs/server.crt

# Test proxy interception
curl -x http://localhost:8080 --cacert infrastructure/certs/aigateway-ca.crt https://api.openai.com/v1/models
```

### Database connection issues

```bash
# Check PostgreSQL is running
docker compose exec postgres pg_isready -U aigateway

# Connect to database manually
docker compose exec postgres psql -U aigateway -d aigateway

# Check initialization was successful
docker compose exec postgres psql -U aigateway -d aigateway -c "\dt"
```

### High memory usage

If the proxy is consuming too much memory, check the resource limits in `docker-compose.prod.yml` and adjust as needed. Consider reducing `LOG_RETENTION_DAYS` if the database is growing too large.

### Proxy not intercepting traffic

1. Verify the client's proxy settings point to the correct host and port (8080)
2. Verify the CA certificate is installed and trusted on the client
3. Check that the AI provider domain is in the `AI_PROVIDER_DOMAINS` list
4. Check proxy logs: `docker compose logs proxy`

## Backup and Recovery

### Database Backup

```bash
# Create a backup
docker compose exec postgres pg_dump -U aigateway aigateway > backup_$(date +%Y%m%d).sql

# Restore from backup
docker compose exec -T postgres psql -U aigateway aigateway < backup_20260101.sql
```

### Full System Backup

Back up these directories:
- `.env` -- environment configuration
- `infrastructure/certs/` -- CA and server certificates
- PostgreSQL data volume (or use pg_dump)
