#!/usr/bin/env bash
# =============================================================================
# AIGateway Interceptor - Test Runner
# =============================================================================
# Runs all test suites (proxy + API) inside their Docker containers.
# Exits with non-zero status if any suite fails.
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Determine docker compose command
if docker compose version &>/dev/null 2>&1; then
    DC="docker compose"
else
    DC="docker-compose"
fi

cd "$PROJECT_ROOT"

echo ""
echo "============================================="
echo " AIGateway Interceptor - Test Runner"
echo "============================================="
echo ""

TOTAL_PASS=0
TOTAL_FAIL=0

# -------------------------------------------------------
# Run Proxy Tests
# -------------------------------------------------------
log_info "Running proxy tests..."
echo "---------------------------------------------"

if $DC exec -T proxy pytest tests/ -v --tb=short 2>&1; then
    log_ok "Proxy tests PASSED."
    TOTAL_PASS=$((TOTAL_PASS + 1))
else
    log_error "Proxy tests FAILED."
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

echo ""

# -------------------------------------------------------
# Run API Tests
# -------------------------------------------------------
log_info "Running API tests..."
echo "---------------------------------------------"

if $DC exec -T api pytest tests/ -v --tb=short 2>&1; then
    log_ok "API tests PASSED."
    TOTAL_PASS=$((TOTAL_PASS + 1))
else
    log_error "API tests FAILED."
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

echo ""

# -------------------------------------------------------
# Run Integration Tests (if available)
# -------------------------------------------------------
if [ -d "$PROJECT_ROOT/tests/integration" ] && ls "$PROJECT_ROOT/tests/integration"/test_*.py &>/dev/null 2>&1; then
    log_info "Running integration tests..."
    echo "---------------------------------------------"

    if $DC exec -T api pytest /app/tests/integration/ -v --tb=short 2>&1; then
        log_ok "Integration tests PASSED."
        TOTAL_PASS=$((TOTAL_PASS + 1))
    else
        log_error "Integration tests FAILED."
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
    fi

    echo ""
fi

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
echo "============================================="
echo " Test Summary"
echo "============================================="
echo ""
echo -e "  Suites passed: ${GREEN}${TOTAL_PASS}${NC}"
echo -e "  Suites failed: ${RED}${TOTAL_FAIL}${NC}"
echo ""

if [ $TOTAL_FAIL -gt 0 ]; then
    log_error "Some test suites failed. See output above for details."
    exit 1
else
    log_ok "All test suites passed!"
    exit 0
fi
