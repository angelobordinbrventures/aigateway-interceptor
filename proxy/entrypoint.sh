#!/usr/bin/env bash
# =============================================================================
# AIGateway Interceptor - Proxy Entrypoint
# =============================================================================
# Configures mitmproxy CA certificates and starts mitmdump.
#
# If custom CA certs are mounted at /certs/ (with mitmproxy-compatible names),
# they are copied into the mitmproxy confdir. Otherwise, mitmproxy will
# auto-generate its own CA on first run.
# =============================================================================

set -euo pipefail

MITMPROXY_CONFDIR="${MITMPROXY_CONFDIR:-/home/mitmproxy/.mitmproxy}"
CERTS_DIR="${CERTS_DIR:-/certs}"
LISTEN_HOST="${LISTEN_HOST:-0.0.0.0}"
LISTEN_PORT="${LISTEN_PORT:-8080}"
SSL_INSECURE="${SSL_INSECURE:-true}"

echo "============================================="
echo " AIGateway Interceptor - Proxy Starting"
echo "============================================="

# Ensure confdir exists
mkdir -p "$MITMPROXY_CONFDIR"

# -------------------------------------------------------
# Copy custom CA certificates if available
# -------------------------------------------------------
if [ -f "$CERTS_DIR/mitmproxy-ca.pem" ]; then
    echo "[entrypoint] Found custom CA at $CERTS_DIR/mitmproxy-ca.pem"
    cp "$CERTS_DIR/mitmproxy-ca.pem" "$MITMPROXY_CONFDIR/mitmproxy-ca.pem"
    echo "[entrypoint] Copied mitmproxy-ca.pem to confdir"

    if [ -f "$CERTS_DIR/mitmproxy-ca-cert.pem" ]; then
        cp "$CERTS_DIR/mitmproxy-ca-cert.pem" "$MITMPROXY_CONFDIR/mitmproxy-ca-cert.pem"
        echo "[entrypoint] Copied mitmproxy-ca-cert.pem to confdir"
    fi

    if [ -f "$CERTS_DIR/mitmproxy-ca-cert.cer" ]; then
        cp "$CERTS_DIR/mitmproxy-ca-cert.cer" "$MITMPROXY_CONFDIR/mitmproxy-ca-cert.cer"
        echo "[entrypoint] Copied mitmproxy-ca-cert.cer to confdir"
    fi

    if [ -f "$CERTS_DIR/mitmproxy-ca-cert.p12" ]; then
        cp "$CERTS_DIR/mitmproxy-ca-cert.p12" "$MITMPROXY_CONFDIR/mitmproxy-ca-cert.p12"
        echo "[entrypoint] Copied mitmproxy-ca-cert.p12 to confdir"
    fi
elif [ -f "$CERTS_DIR/aigateway-ca.key" ] && [ -f "$CERTS_DIR/aigateway-ca.crt" ]; then
    # Build mitmproxy-ca.pem from separate key + cert files
    echo "[entrypoint] Found aigateway CA key+cert, building mitmproxy-ca.pem"
    cat "$CERTS_DIR/aigateway-ca.key" "$CERTS_DIR/aigateway-ca.crt" \
        > "$MITMPROXY_CONFDIR/mitmproxy-ca.pem"
    cp "$CERTS_DIR/aigateway-ca.crt" "$MITMPROXY_CONFDIR/mitmproxy-ca-cert.pem"
    echo "[entrypoint] Generated mitmproxy-compatible CA files in confdir"
else
    echo "[entrypoint] No custom CA found at $CERTS_DIR — mitmproxy will auto-generate"
fi

# -------------------------------------------------------
# Build mitmdump arguments
# -------------------------------------------------------
MITM_ARGS=(
    "--listen-host" "$LISTEN_HOST"
    "--listen-port" "$LISTEN_PORT"
    "--set" "confdir=$MITMPROXY_CONFDIR"
    "-s" "main.py"
)

if [ "$SSL_INSECURE" = "true" ]; then
    MITM_ARGS+=("--ssl-insecure")
    echo "[entrypoint] SSL upstream verification DISABLED (dev mode)"
fi

echo "[entrypoint] Listening on $LISTEN_HOST:$LISTEN_PORT"
echo "[entrypoint] Confdir: $MITMPROXY_CONFDIR"
echo "============================================="

exec mitmdump "${MITM_ARGS[@]}"
