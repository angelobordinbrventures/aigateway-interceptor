#!/usr/bin/env bash
# =============================================================================
# AIGateway Interceptor - Development Environment Setup
# =============================================================================
# This script bootstraps the full development stack:
#   1. Checks prerequisites
#   2. Generates TLS certificates (if missing)
#   3. Creates .env from template (if missing)
#   4. Builds and starts all Docker services
#   5. Waits for services to become healthy
#   6. Runs smoke tests
#   7. Prints access URLs
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="$PROJECT_ROOT/infrastructure/certs"
HEALTH_TIMEOUT=120  # seconds

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# -------------------------------------------------------
# Step 1: Check prerequisites
# -------------------------------------------------------
echo ""
echo "============================================="
echo " AIGateway Interceptor - Dev Setup"
echo "============================================="
echo ""

log_info "Checking prerequisites..."

MISSING=()

if ! command -v docker &>/dev/null; then
    MISSING+=("docker")
fi

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
    MISSING+=("docker-compose")
fi

if ! command -v openssl &>/dev/null; then
    MISSING+=("openssl")
fi

if [ ${#MISSING[@]} -gt 0 ]; then
    log_error "Missing prerequisites: ${MISSING[*]}"
    echo ""
    echo "Please install the missing tools and try again."
    echo "  - Docker:         https://docs.docker.com/get-docker/"
    echo "  - Docker Compose: https://docs.docker.com/compose/install/"
    echo "  - OpenSSL:        Usually pre-installed on macOS/Linux"
    exit 1
fi

log_ok "All prerequisites found."

# Determine docker compose command
if docker compose version &>/dev/null 2>&1; then
    DC="docker compose"
else
    DC="docker-compose"
fi

# -------------------------------------------------------
# Step 2: Generate certificates if not present
# -------------------------------------------------------
log_info "Checking TLS certificates..."

if [ ! -f "$CERT_DIR/aigateway-ca.crt" ] || [ ! -f "$CERT_DIR/server.crt" ]; then
    log_warn "Certificates not found. Generating..."
    bash "$CERT_DIR/generate-ca.sh" "$CERT_DIR"
    log_ok "Certificates generated."
else
    log_ok "Certificates already exist."
fi

# -------------------------------------------------------
# Step 3: Create .env file if not present
# -------------------------------------------------------
log_info "Checking environment configuration..."

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        log_ok "Created .env from .env.example"
        log_warn "Review .env and update secrets before going to production!"
    else
        log_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
else
    log_ok ".env file already exists."
fi

# -------------------------------------------------------
# Step 4: Build and start services
# -------------------------------------------------------
log_info "Building and starting Docker services..."

cd "$PROJECT_ROOT"
$DC up --build -d

log_ok "Docker services started."

# -------------------------------------------------------
# Step 5: Wait for services to be healthy
# -------------------------------------------------------
log_info "Waiting for services to become healthy (timeout: ${HEALTH_TIMEOUT}s)..."

declare -A SERVICES=(
    ["postgres"]="pg_isready"
    ["redis"]="redis-cli ping"
    ["api"]="curl -sf http://localhost:8000/health"
    ["nginx"]="curl -sf http://localhost/health"
)

wait_for_service() {
    local name="$1"
    local check_cmd="$2"
    local elapsed=0
    local interval=3

    while [ $elapsed -lt $HEALTH_TIMEOUT ]; do
        if eval "$check_cmd" &>/dev/null; then
            log_ok "$name is healthy."
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    log_error "$name did not become healthy within ${HEALTH_TIMEOUT}s."
    return 1
}

FAILED=0

# Wait for postgres via docker exec
log_info "Checking postgres..."
ELAPSED=0
while [ $ELAPSED -lt $HEALTH_TIMEOUT ]; do
    if $DC exec -T postgres pg_isready -U aigateway &>/dev/null; then
        log_ok "postgres is healthy."
        break
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done
if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
    log_error "postgres did not become healthy."
    FAILED=1
fi

# Wait for redis via docker exec
log_info "Checking redis..."
ELAPSED=0
while [ $ELAPSED -lt $HEALTH_TIMEOUT ]; do
    if $DC exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
        log_ok "redis is healthy."
        break
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done
if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
    log_error "redis did not become healthy."
    FAILED=1
fi

# Wait for API
log_info "Checking API..."
ELAPSED=0
while [ $ELAPSED -lt $HEALTH_TIMEOUT ]; do
    if curl -sf http://localhost:8000/health &>/dev/null; then
        log_ok "API is healthy."
        break
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done
if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
    log_error "API did not become healthy."
    FAILED=1
fi

# Wait for Nginx gateway
log_info "Checking nginx gateway..."
ELAPSED=0
while [ $ELAPSED -lt $HEALTH_TIMEOUT ]; do
    if curl -sf http://localhost/health &>/dev/null; then
        log_ok "nginx gateway is healthy."
        break
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done
if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
    log_error "nginx gateway did not become healthy."
    FAILED=1
fi

if [ $FAILED -ne 0 ]; then
    log_error "Some services failed to start. Check logs with: $DC logs"
    exit 1
fi

# -------------------------------------------------------
# Step 6: Smoke tests
# -------------------------------------------------------
echo ""
log_info "Running smoke tests..."

SMOKE_PASS=0
SMOKE_FAIL=0

smoke_test() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"

    local code
    code=$(curl -sf -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$code" = "$expected_code" ]; then
        log_ok "PASS: $name (HTTP $code)"
        SMOKE_PASS=$((SMOKE_PASS + 1))
    else
        log_error "FAIL: $name (expected $expected_code, got $code)"
        SMOKE_FAIL=$((SMOKE_FAIL + 1))
    fi
}

smoke_test "Gateway Health"    "http://localhost/health"
smoke_test "API Health"        "http://localhost:8000/health"
smoke_test "API via Gateway"   "http://localhost/api/health"
smoke_test "Dashboard"         "http://localhost/"

echo ""
log_info "Smoke tests: $SMOKE_PASS passed, $SMOKE_FAIL failed."

# -------------------------------------------------------
# Step 7: Print access URLs
# -------------------------------------------------------
echo ""
echo "============================================="
echo " AIGateway Interceptor is running!"
echo "============================================="
echo ""
echo "  Dashboard:    http://localhost"
echo "  API:          http://localhost/api/"
echo "  API (direct): http://localhost:8000"
echo "  Proxy:        localhost:8080 (configure as HTTP proxy)"
echo ""
echo "  Default login:"
echo "    Username: admin"
echo "    Password: admin123"
echo ""
echo "  Useful commands:"
echo "    View logs:     $DC logs -f"
echo "    Stop:          $DC down"
echo "    Rebuild:       $DC up --build -d"
echo "    Run tests:     ./scripts/run-tests.sh"
echo ""
echo "  To intercept traffic, configure your HTTP proxy to:"
echo "    Host: localhost"
echo "    Port: 8080"
echo "    Install CA cert: ./scripts/install-ca-cert.sh"
echo ""
