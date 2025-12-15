#!/bin/bash
# MT5 Installation, Configuration, and Auto-Login
# Merged from: 30_mt5_install.sh, 31_mt5_config.sh, 32_mt5_login.sh
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# ============================================================
# Phase 1: Generate Configuration (if credentials provided)
# ============================================================
generate_config() {
    if [ -z "${MT5_LOGIN:-}" ] || [ -z "${MT5_PASSWORD:-}" ] || [ -z "${MT5_SERVER:-}" ]; then
        log INFO "[mt5] No credentials provided; skipping config generation"
        return 0
    fi

    log INFO "[mt5] Generating startup configuration..."
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

    log INFO "[mt5] Created startup config at $MT5_STARTUP_INI"

    # Create/update common.ini with essential settings
    COMMON_INI="$MT5_CONFIG_DIR/common.ini"
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

    log INFO "[mt5] Auto-login configured for account ${MT5_LOGIN} on ${MT5_SERVER}"
}

# ============================================================
# Phase 2: Install/Upgrade MetaTrader 5
# Always runs installer to ensure latest version
# ============================================================
install_mt5() {
    MT5_SETUP="$WINEPREFIX/drive_c/mt5setup.exe"

    if [ -e "$mt5file" ]; then
        log INFO "[mt5] Found existing installation at $mt5file"
        log INFO "[mt5] Running upgrade to ensure latest version..."
    else
        log INFO "[mt5] Not found. Installing..."
    fi

    # Set Windows version to Win10
    "$wine_executable" reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win10" /f 2>/dev/null || true

    # Get MT5 installer (always download fresh for upgrades)
    log INFO "[mt5] Getting installer..."
    get_file "mt5setup.exe" "$mt5setup_url" "$MT5_SETUP"

    # Install/Upgrade MT5 silently
    log INFO "[mt5] Running installer (silent mode)..."
    "$wine_executable" "$MT5_SETUP" "/auto" &
    INSTALLER_PID=$!
    if ! wait $INSTALLER_PID; then
        log WARN "[mt5] Installer process returned non-zero (may be OK for upgrades)"
    fi

    # Cleanup installer
    rm -f "$MT5_SETUP"

    # Verify installation
    if [ ! -e "$mt5file" ]; then
        log ERROR "[mt5] Installation failed. File not found: $mt5file"
        return 1
    fi
    if [ ! -f "$mt5file" ]; then
        log ERROR "[mt5] Installation failed. Not a regular file: $mt5file"
        return 1
    fi
    log INFO "[mt5] Installation/upgrade successful: $mt5file"
}

# ============================================================
# Phase 3: Launch MT5
# ============================================================
launch_mt5() {
    if [ ! -e "$mt5file" ]; then
        log ERROR "[mt5] Cannot launch - not installed"
        return 1
    fi

    log INFO "[mt5] Launching terminal..."

    # Build MT5 launch arguments
    MT5_ARGS="/portable"  # Always use portable mode for Docker

    # Auto-login configuration (explicit logging of which method is used)
    if [ -f "$MT5_STARTUP_INI" ]; then
        MT5_ARGS="$MT5_ARGS /config:\"C:\\Program Files\\MetaTrader 5\\Config\\startup.ini\""
        log INFO "[mt5] Auto-login: Using config file"
    elif [ -n "${MT5_LOGIN:-}" ] && [ -n "${MT5_PASSWORD:-}" ] && [ -n "${MT5_SERVER:-}" ]; then
        MT5_ARGS="$MT5_ARGS /login:${MT5_LOGIN} /password:${MT5_PASSWORD} /server:${MT5_SERVER}"
        log INFO "[mt5] Auto-login: Using CLI args for account ${MT5_LOGIN}"
    else
        log INFO "[mt5] Auto-login: Disabled (no config or credentials)"
    fi

    # Launch MT5 in portable mode with config
    log INFO "[mt5] Starting: $MT5_ARGS"
    "$wine_executable" "$mt5file" $MT5_ARGS &

    # Wait for MT5 to initialize
    sleep 5
}

# ============================================================
# Phase 4: Python API Login (after Python is installed)
# Called separately after 40_python_wine.sh
# ============================================================
python_api_login() {
    # Skip if no credentials provided
    if [ -z "${MT5_LOGIN:-}" ] || [ -z "${MT5_PASSWORD:-}" ] || [ -z "${MT5_SERVER:-}" ]; then
        log INFO "[mt5-login] No credentials provided; skipping"
        return 0
    fi

    # Skip if already logged in (prevents duplicate login attempts on restart)
    if [ -f "$MT5_LOGGED_IN_MARKER" ]; then
        log INFO "[mt5-login] Already logged in (marker exists); skipping"
        return 0
    fi

    log INFO "[mt5-login] Waiting for terminal to initialize..."

    # Wait for MT5 terminal to start (max 90 seconds)
    MAX_WAIT=90
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if pgrep -f "terminal64.exe" > /dev/null 2>&1; then
            log INFO "[mt5-login] Terminal detected, waiting for full initialization..."
            sleep 15  # Give MT5 time to fully initialize and connect to server
            break
        fi
        sleep 3
        WAITED=$((WAITED + 3))
    done

    if [ $WAITED -ge $MAX_WAIT ]; then
        log ERROR "[mt5-login] Terminal did not start within ${MAX_WAIT}s"
        return 1
    fi

    # MT5 executable path for Python API
    MT5_PATH="C:\\\\Program Files\\\\MetaTrader 5\\\\terminal64.exe"

    # Use Wine Python to login via MetaTrader5 API
    log INFO "[mt5-login] Attempting login for account ${MT5_LOGIN} on ${MT5_SERVER}..."

    "$wine_executable" python -c "
import MetaTrader5 as mt5
import sys
import time

# Credentials
login = int('${MT5_LOGIN}')
password = '${MT5_PASSWORD}'
server = '${MT5_SERVER}'
path = r'${MT5_PATH}'

print(f'MT5 Python API Login')
print(f'  Path: {path}')
print(f'  Server: {server}')
print(f'  Account: {login}')
print()

# Try multiple times as MT5 might still be initializing
max_attempts = 10
for attempt in range(max_attempts):
    print(f'Attempt {attempt + 1}/{max_attempts}...')

    # Initialize with full parameters
    result = mt5.initialize(
        path=path,
        login=login,
        password=password,
        server=server,
        timeout=30000,  # 30 second timeout
        portable=True   # Use portable mode
    )

    if result:
        account = mt5.account_info()
        if account and account.login > 0:
            print()
            print('=' * 50)
            print('SUCCESS: MT5 Login Successful!')
            print('=' * 50)
            print(f'  Account: {account.login}')
            print(f'  Server: {account.server}')
            print(f'  Name: {account.name}')
            print(f'  Balance: {account.balance} {account.currency}')
            print(f'  Leverage: 1:{account.leverage}')
            print(f'  Trade Mode: {account.trade_mode}')
            print('=' * 50)

            # Keep connection alive - don't shutdown
            sys.exit(0)
        else:
            error = mt5.last_error()
            print(f'  Initialized but no account: {error}')
    else:
        error = mt5.last_error()
        print(f'  Failed: {error}')

    mt5.shutdown()
    time.sleep(5)

print()
print('FAILED: Could not login after all attempts')
print('Please check:')
print('  1. Credentials are correct')
print('  2. Server name matches exactly')
print('  3. MT5 terminal can reach the server')
sys.exit(1)
" 2>&1

    LOGIN_RESULT=$?
    if [ $LOGIN_RESULT -eq 0 ]; then
        log INFO "[mt5-login] Auto-login successful via Python API"
        touch "$MT5_LOGGED_IN_MARKER"
    else
        log ERROR "[mt5-login] Auto-login failed (code: $LOGIN_RESULT)"
        log ERROR "[mt5-login] Credentials were provided but login failed - check credentials"
        return 1
    fi
}

# ============================================================
# Main execution
# ============================================================
case "${1:-install}" in
    config)
        generate_config
        ;;
    install)
        generate_config
        install_mt5
        launch_mt5
        ;;
    login)
        python_api_login
        ;;
    *)
        log ERROR "Unknown command: $1 (use: config, install, login)"
        exit 1
        ;;
esac
