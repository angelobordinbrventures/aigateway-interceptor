#!/usr/bin/env bash
# =============================================================================
# AIGateway Interceptor - CA Certificate Generator
# =============================================================================
# Generates a self-signed Certificate Authority (CA) and a server certificate
# signed by that CA. The CA cert is installed on client machines so that the
# mitmproxy interception is transparent (no browser warnings).
#
# Output files:
#   aigateway-ca.key  - CA private key (keep secret)
#   aigateway-ca.crt  - CA certificate (distribute to clients)
#   server.key        - Server private key
#   server.crt        - Server certificate signed by CA
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${1:-$SCRIPT_DIR}"

CA_KEY="$CERT_DIR/aigateway-ca.key"
CA_CRT="$CERT_DIR/aigateway-ca.crt"
SERVER_KEY="$CERT_DIR/server.key"
SERVER_CSR="$CERT_DIR/server.csr"
SERVER_CRT="$CERT_DIR/server.crt"
SERVER_EXT="$CERT_DIR/server.ext"

CA_SUBJECT="/C=BR/ST=Sao Paulo/L=Sao Paulo/O=AIGateway Interceptor/OU=Security/CN=AIGateway Root CA"
SERVER_SUBJECT="/C=BR/ST=Sao Paulo/L=Sao Paulo/O=AIGateway Interceptor/OU=Security/CN=aigateway.local"

CA_DAYS=3650    # 10 years
SERVER_DAYS=825 # ~2.25 years (Apple max)

echo "============================================="
echo " AIGateway Interceptor - Certificate Generator"
echo "============================================="
echo ""
echo "Output directory: $CERT_DIR"
echo ""

mkdir -p "$CERT_DIR"

# -------------------------------------------------------
# Step 1: Generate CA private key
# -------------------------------------------------------
echo "[1/5] Generating CA private key (RSA 4096)..."
openssl genrsa -out "$CA_KEY" 4096 2>/dev/null

# -------------------------------------------------------
# Step 2: Generate self-signed CA certificate
# -------------------------------------------------------
echo "[2/5] Generating CA certificate (valid $CA_DAYS days)..."
openssl req -x509 -new -nodes \
    -key "$CA_KEY" \
    -sha256 \
    -days "$CA_DAYS" \
    -subj "$CA_SUBJECT" \
    -out "$CA_CRT"

# -------------------------------------------------------
# Step 3: Generate server private key
# -------------------------------------------------------
echo "[3/5] Generating server private key (RSA 2048)..."
openssl genrsa -out "$SERVER_KEY" 2048 2>/dev/null

# -------------------------------------------------------
# Step 4: Generate server CSR
# -------------------------------------------------------
echo "[4/5] Generating server certificate signing request..."
openssl req -new \
    -key "$SERVER_KEY" \
    -subj "$SERVER_SUBJECT" \
    -out "$SERVER_CSR"

# Server certificate extensions (SAN)
cat > "$SERVER_EXT" <<EXTEOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = aigateway.local
DNS.2 = *.aigateway.local
DNS.3 = localhost
DNS.4 = proxy
DNS.5 = api
DNS.6 = dashboard
DNS.7 = nginx
IP.1 = 127.0.0.1
IP.2 = 0.0.0.0
EXTEOF

# -------------------------------------------------------
# Step 5: Sign server certificate with CA
# -------------------------------------------------------
echo "[5/5] Signing server certificate with CA..."
openssl x509 -req \
    -in "$SERVER_CSR" \
    -CA "$CA_CRT" \
    -CAkey "$CA_KEY" \
    -CAcreateserial \
    -out "$SERVER_CRT" \
    -days "$SERVER_DAYS" \
    -sha256 \
    -extfile "$SERVER_EXT" 2>/dev/null

# Cleanup temporary files
rm -f "$SERVER_CSR" "$SERVER_EXT" "$CERT_DIR/aigateway-ca.srl"

# Set permissions
chmod 600 "$CA_KEY" "$SERVER_KEY"
chmod 644 "$CA_CRT" "$SERVER_CRT"

# -------------------------------------------------------
# Step 6: Generate mitmproxy-compatible CA files
# -------------------------------------------------------
MITM_CA_PEM="$CERT_DIR/mitmproxy-ca.pem"
MITM_CA_CERT="$CERT_DIR/mitmproxy-ca-cert.pem"

echo "[6/6] Generating mitmproxy-compatible CA files..."

# mitmproxy-ca.pem: combined private key + certificate
cat "$CA_KEY" "$CA_CRT" > "$MITM_CA_PEM"
chmod 600 "$MITM_CA_PEM"

# mitmproxy-ca-cert.pem: certificate only (for client distribution)
cp "$CA_CRT" "$MITM_CA_CERT"
chmod 644 "$MITM_CA_CERT"

echo ""
echo "============================================="
echo " Certificates generated successfully!"
echo "============================================="
echo ""
echo "  CA Key:              $CA_KEY"
echo "  CA Certificate:      $CA_CRT"
echo "  Server Key:          $SERVER_KEY"
echo "  Server Cert:         $SERVER_CRT"
echo "  mitmproxy CA (pem):  $MITM_CA_PEM"
echo "  mitmproxy CA (cert): $MITM_CA_CERT"
echo ""
echo "Next steps:"
echo "  1. Distribute '$CA_CRT' to client machines"
echo "  2. Run 'scripts/install-ca-cert.sh' on each client"
echo "  3. Configure proxy to use server.key and server.crt"
echo "  4. mitmproxy-compatible files are ready at $CERT_DIR"
echo ""
