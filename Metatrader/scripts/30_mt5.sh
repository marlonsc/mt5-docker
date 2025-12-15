#!/bin/bash
# MT5 Installation and Configuration
# Downloads and installs LATEST versions at every startup
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# ============================================================
# Install MetaTrader5 pip package (LATEST VERSION)
# ============================================================
install_mt5_pip() {
    log INFO "[mt5] Installing MetaTrader5 pip package (latest)..."

    if [ ! -f "$WINE_PYTHON_PATH" ]; then
        log ERROR "[mt5] FATAL: Wine Python not found at $WINE_PYTHON_PATH"
        return 1
    fi

    # Install MetaTrader5 without upgrading numpy (numpy 1.26.4 is Wine-compatible)
    # numpy 2.x uses ucrtbase.dll functions Wine hasn't implemented
    "$wine_executable" "$WINE_PYTHON_PATH" -m pip install --upgrade --no-cache-dir --no-deps \
        MetaTrader5 2>&1 || {
        log ERROR "[mt5] MetaTrader5 pip installation failed"
        return 1
    }

    "$wine_executable" "$WINE_PYTHON_PATH" -c "import MetaTrader5; print(f'MetaTrader5 {MetaTrader5.__version__} installed')" 2>/dev/null || {
        log ERROR "[mt5] MetaTrader5 import verification failed"
        return 1
    }
}

# ============================================================
# Install MetaTrader 5 Terminal (LATEST VERSION)
# Downloads and runs installer at every startup
# ============================================================
install_mt5_terminal() {
    log INFO "[mt5] Installing MetaTrader 5 terminal (latest)..."

    MT5_SETUP="/tmp/mt5setup.exe"

    # Always download fresh installer for latest version
    log INFO "[mt5] Downloading mt5setup.exe..."
    curl -fSL -o "$MT5_SETUP" "$mt5setup_url" || {
        log ERROR "[mt5] Failed to download mt5setup.exe"
        return 1
    }

    # Run installer (silent mode)
    log INFO "[mt5] Running installer..."
    "$wine_executable" "$MT5_SETUP" "/auto" 2>&1 || true
    sleep 10
    rm -f "$MT5_SETUP"

    if [ -e "$mt5file" ]; then
        log INFO "[mt5] Terminal installed: $mt5file"
    else
        log ERROR "[mt5] Terminal installation failed"
        return 1
    fi
}

# ============================================================
# Generate Configuration (if credentials provided)
# ============================================================
generate_config() {
    if [ -z "${MT5_LOGIN:-}" ] || [ -z "${MT5_PASSWORD:-}" ] || [ -z "${MT5_SERVER:-}" ]; then
        return 0
    fi

    log INFO "[mt5] Generating config for account ${MT5_LOGIN}..."
    mkdir -p "$MT5_CONFIG_DIR"

    cat > "$MT5_STARTUP_INI" << EOF
[Common]
Login=${MT5_LOGIN}
Password=${MT5_PASSWORD}
Server=${MT5_SERVER}
ProxyEnable=0
NewsEnable=1
KeepPrivate=1

[Experts]
Enabled=1
AllowLiveTrading=1
AllowDllImport=1
EOF
}

# ============================================================
# Launch MT5
# ============================================================
launch_mt5() {
    if [ ! -e "$mt5file" ]; then
        log ERROR "[mt5] Cannot launch - not installed"
        return 1
    fi

    log INFO "[mt5] Launching terminal..."

    MT5_ARGS="/portable"
    if [ -f "$MT5_STARTUP_INI" ]; then
        MT5_ARGS="$MT5_ARGS /config:\"C:\\Program Files\\MetaTrader 5\\Config\\startup.ini\""
    fi

    "$wine_executable" "$mt5file" $MT5_ARGS &
    sleep 5
}

# ============================================================
# Main execution
# ============================================================
install_mt5_pip
install_mt5_terminal
generate_config
launch_mt5
