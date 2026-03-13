#!/usr/bin/env bash
# =============================================================================
# AIGateway Interceptor - CA Certificate Installer
# =============================================================================
# Installs the AIGateway CA certificate into the system trust store so that
# intercepted HTTPS traffic is trusted by browsers and CLI tools.
#
# Supports: macOS, Debian/Ubuntu, RHEL/CentOS/Fedora, Windows (via WSL)
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CA_CERT="${1:-$PROJECT_ROOT/infrastructure/certs/aigateway-ca.crt}"

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

echo ""
echo "============================================="
echo " AIGateway CA Certificate Installer"
echo "============================================="
echo ""

# Verify certificate exists
if [ ! -f "$CA_CERT" ]; then
    log_error "CA certificate not found: $CA_CERT"
    echo ""
    echo "Generate it first with:"
    echo "  ./infrastructure/certs/generate-ca.sh"
    exit 1
fi

log_info "Certificate: $CA_CERT"
echo ""

# -------------------------------------------------------
# Detect OS and install
# -------------------------------------------------------
install_macos() {
    log_info "Detected: macOS"
    log_info "Installing CA certificate to System Keychain..."
    log_warn "You may be prompted for your password."
    echo ""

    sudo security add-trusted-cert \
        -d \
        -r trustRoot \
        -k /Library/Keychains/System.keychain \
        "$CA_CERT"

    log_ok "CA certificate installed to macOS System Keychain."
    echo ""
    log_info "Browser notes:"
    echo "  - Safari: Works immediately (uses System Keychain)."
    echo "  - Chrome: Works immediately (uses System Keychain)."
    echo "  - Firefox: Uses its own store. Import manually:"
    echo "      Settings > Privacy & Security > Certificates > View Certificates"
    echo "      > Authorities > Import > select aigateway-ca.crt"
    echo "      > Check 'Trust this CA to identify websites'"
}

install_debian() {
    log_info "Detected: Debian/Ubuntu"
    log_info "Installing CA certificate to system trust store..."
    echo ""

    sudo cp "$CA_CERT" /usr/local/share/ca-certificates/aigateway-ca.crt
    sudo update-ca-certificates

    log_ok "CA certificate installed."
    echo ""
    log_info "Browser notes:"
    echo "  - Chrome/Chromium: May need restart. If not trusted:"
    echo "      chrome://settings/certificates > Authorities > Import"
    echo "  - Firefox: Uses its own store. Import manually:"
    echo "      Settings > Privacy & Security > Certificates > View Certificates"
    echo "      > Authorities > Import > select aigateway-ca.crt"
}

install_rhel() {
    log_info "Detected: RHEL/CentOS/Fedora"
    log_info "Installing CA certificate to system trust store..."
    echo ""

    sudo cp "$CA_CERT" /etc/pki/ca-trust/source/anchors/aigateway-ca.crt
    sudo update-ca-trust extract

    log_ok "CA certificate installed."
    echo ""
    log_info "Browser notes:"
    echo "  - Chrome/Chromium: May need restart."
    echo "  - Firefox: Uses its own store. Import manually."
}

install_wsl() {
    log_info "Detected: Windows (WSL)"
    log_info "Installing CA certificate to Windows trust store..."
    echo ""

    # Convert path for Windows
    WIN_CERT=$(wslpath -w "$CA_CERT")

    # Install to Windows certificate store
    powershell.exe -Command "Import-Certificate -FilePath '$WIN_CERT' -CertStoreLocation 'Cert:\\LocalMachine\\Root'" 2>/dev/null || {
        log_warn "PowerShell import failed. Trying certutil..."
        certutil.exe -addstore -f "ROOT" "$WIN_CERT" 2>/dev/null || {
            log_error "Automatic installation failed."
            echo ""
            echo "Manual installation for Windows:"
            echo "  1. Double-click the .crt file"
            echo "  2. Click 'Install Certificate'"
            echo "  3. Select 'Local Machine'"
            echo "  4. Select 'Place all certificates in the following store'"
            echo "  5. Browse > 'Trusted Root Certification Authorities'"
            echo "  6. Click Finish"
            exit 1
        }
    }

    log_ok "CA certificate installed to Windows trust store."

    # Also install in WSL Linux trust store
    log_info "Also installing in WSL Linux trust store..."
    if [ -d /usr/local/share/ca-certificates ]; then
        sudo cp "$CA_CERT" /usr/local/share/ca-certificates/aigateway-ca.crt
        sudo update-ca-certificates 2>/dev/null || true
    fi
}

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    install_macos
elif grep -qi microsoft /proc/version 2>/dev/null; then
    install_wsl
elif [ -f /etc/debian_version ]; then
    install_debian
elif [ -f /etc/redhat-release ] || [ -f /etc/fedora-release ]; then
    install_rhel
else
    log_error "Unsupported OS: $OSTYPE"
    echo ""
    echo "Manual installation:"
    echo "  Copy '$CA_CERT' to your system's CA trust store and update."
    echo ""
    echo "  Debian/Ubuntu: /usr/local/share/ca-certificates/ + update-ca-certificates"
    echo "  RHEL/CentOS:   /etc/pki/ca-trust/source/anchors/ + update-ca-trust extract"
    echo "  macOS:          security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain <cert>"
    exit 1
fi

echo ""
echo "============================================="
echo " Verification"
echo "============================================="
echo ""
echo "Test that the certificate is trusted:"
echo "  curl -v https://aigateway.local 2>&1 | grep -i 'SSL certificate verify ok'"
echo ""
echo "Or configure your proxy and test:"
echo "  export https_proxy=http://localhost:8080"
echo "  curl https://api.openai.com/v1/models"
echo ""
