#!/bin/bash
# MT5 Configuration Generator
# Creates startup.ini file for auto-login and auto-trading configuration
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

MT5_CONFIG_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/Config"
MT5_STARTUP_INI="$MT5_CONFIG_DIR/startup.ini"

# Skip if no credentials provided
if [ -z "${MT5_LOGIN:-}" ] || [ -z "${MT5_PASSWORD:-}" ] || [ -z "${MT5_SERVER:-}" ]; then
    log INFO "[3.1/9] No MT5 credentials provided; skipping config generation"
    exit 0
fi

log INFO "[3.1/9] Generating MT5 startup configuration..."

# Ensure config directory exists
mkdir -p "$MT5_CONFIG_DIR"

# Generate startup.ini with auto-login and auto-trading settings
cat > "$MT5_STARTUP_INI" << EOF
; MT5 Startup Configuration - Auto-generated
; Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)

[Common]
; Account credentials
Login=${MT5_LOGIN}
Password=${MT5_PASSWORD}
Server=${MT5_SERVER}

; Proxy settings (disabled)
ProxyEnable=0
ProxyType=0
ProxyAddress=
ProxyLogin=
ProxyPassword=

; Other settings
NewsEnable=1
CertInstall=0

; Keep settings on startup (important for auto-login)
KeepPrivate=1

[Experts]
; Enable automated trading
Enabled=1
AllowLiveTrading=1
AllowDllImport=1
Account=0
Profile=0

[Charts]
; Chart settings
MaxBars=100000
PrintColor=0
SaveDeleted=0

[Objects]
ShowPropertiesOnCreate=0
SelectOneClick=1
MagnetSens=10

[StartUp]
; No auto-launch EA by default (can be configured)
; Expert=
; Symbol=EURUSD
; Period=H1
; Template=

[Tester]
; Strategy tester settings
UseLocal=1
UseRemote=0
UseCloud=0
EOF

log INFO "[3.1/9] Created startup configuration at $MT5_STARTUP_INI"

# Also update common.ini if it exists (for persistent settings)
COMMON_INI="$MT5_CONFIG_DIR/common.ini"
if [ -f "$COMMON_INI" ]; then
    log INFO "[3.1/9] Updating common.ini with login settings..."
    # Backup original
    cp "$COMMON_INI" "$COMMON_INI.bak" 2>/dev/null || true
fi

# Create/update common.ini with essential settings
cat > "$COMMON_INI" << EOF
; MT5 Common Configuration - Auto-generated
[Common]
Login=${MT5_LOGIN}
Password=${MT5_PASSWORD}
Server=${MT5_SERVER}
KeepPrivate=1
NewsEnable=1

[Experts]
Enabled=1
AllowLiveTrading=1
AllowDllImport=1
EOF

log INFO "[3.1/9] Configuration files generated successfully"
log INFO "[3.1/9] Auto-login: account ${MT5_LOGIN} on ${MT5_SERVER}"
