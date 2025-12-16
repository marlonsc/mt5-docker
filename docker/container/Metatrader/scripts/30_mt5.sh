#!/bin/bash
# MT5 Installation and Configuration
# =============================================================================
# Package Policy:
#   - MetaTrader5 PIP: ALWAYS reinstall (get latest from PyPI)
#   - Server module: Copied directly (no pip install)
#   - MT5 Terminal: IDEMPOTENT (skip if already installed)
#   - Config: IDEMPOTENT (skip if same credentials)
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

MT5_INSTALL_TIMEOUT=60

# ============================================================
# Install MetaTrader5 Python package (ALWAYS FRESH)
# ============================================================
install_mt5_pip() {
    if [ ! -f "$WINE_PYTHON_PATH" ]; then
        log ERROR "[mt5] FATAL: Wine Python not found at $WINE_PYTHON_PATH"
        return 1
    fi

    log INFO "[mt5] Installing MetaTrader5 pip package..."

    # Build pip install arguments based on MT5_UPDATE setting
    pip_args="--no-deps"
    if [ "${MT5_UPDATE:-1}" = "1" ]; then
        pip_args="--upgrade --no-cache-dir ${pip_args}"
        log INFO "[mt5] Installing MetaTrader5 (update enabled, fresh install)..."
    else
        log INFO "[mt5] Installing MetaTrader5 (update disabled, using cached)..."
    fi

    "$wine_executable" "$WINE_PYTHON_PATH" -m pip install ${pip_args} \
        MetaTrader5 2>&1 || {
        log ERROR "[mt5] MetaTrader5 installation failed"
        return 1
    }

    # Verify imports work
    log INFO "[mt5] Verifying package imports..."
    "$wine_executable" "$WINE_PYTHON_PATH" -c "
import MetaTrader5
import rpyc
import numpy
print(f'MetaTrader5 {MetaTrader5.__version__}')
print(f'rpyc {rpyc.__version__}')
print(f'numpy {numpy.__version__}')
" 2>/dev/null || {
        log ERROR "[mt5] Package verification failed"
        return 1
    }

    log INFO "[mt5] Pip packages installed successfully"
}

# ============================================================
# Install MetaTrader 5 Terminal (IDEMPOTENT)
# Skips if terminal64.exe already exists
# ============================================================
install_mt5_terminal() {
    if [ -e "$mt5file" ]; then
        log INFO "[mt5] Terminal already installed: $mt5file"
        return 0
    fi

    log INFO "[mt5] Installing MetaTrader 5 terminal..."

    MT5_SETUP="/tmp/mt5setup.exe"

    # Download installer
    log INFO "[mt5] Downloading mt5setup.exe..."
    curl -fSL -o "$MT5_SETUP" "$mt5setup_url" || {
        log ERROR "[mt5] Failed to download mt5setup.exe"
        return 1
    }

    # Run installer with timeout
    log INFO "[mt5] Running installer (timeout: ${MT5_INSTALL_TIMEOUT}s)..."
    "$wine_executable" "$MT5_SETUP" "/auto" &
    INSTALLER_PID=$!

    local elapsed=0
    while [ $elapsed -lt $MT5_INSTALL_TIMEOUT ]; do
        if ! kill -0 $INSTALLER_PID 2>/dev/null; then
            log INFO "[mt5] Installer completed"
            break
        fi

        if [ -e "$mt5file" ]; then
            log INFO "[mt5] Terminal detected - killing installer"
            kill $INSTALLER_PID 2>/dev/null || true
            pkill -f "mt5setup" 2>/dev/null || true
            wineserver -k 2>/dev/null || true
            sleep 2
            break
        fi

        sleep 5
        elapsed=$((elapsed + 5))
    done

    # Cleanup
    if kill -0 $INSTALLER_PID 2>/dev/null; then
        log WARN "[mt5] Installer timeout - forcing kill"
        kill $INSTALLER_PID 2>/dev/null || true
        pkill -f "mt5setup" 2>/dev/null || true
        wineserver -k 2>/dev/null || true
        sleep 2
    fi

    rm -f "$MT5_SETUP"

    if [ -e "$mt5file" ]; then
        log INFO "[mt5] Terminal installed: $mt5file"
    else
        log ERROR "[mt5] Terminal installation failed"
        return 1
    fi
}

# ============================================================
# Generate Configuration (IDEMPOTENT)
# Regenerates only if credentials changed
# ============================================================
generate_config() {
    if [ -z "${MT5_LOGIN:-}" ] || [ -z "${MT5_PASSWORD:-}" ] || [ -z "${MT5_SERVER:-}" ]; then
        log INFO "[mt5] No credentials provided, skipping config"
        return 0
    fi

    # Skip if config already exists with same credentials
    if [ -f "$MT5_STARTUP_INI" ]; then
        if grep -q "Login=${MT5_LOGIN}" "$MT5_STARTUP_INI" 2>/dev/null; then
            log INFO "[mt5] Config already exists for ${MT5_LOGIN}@${MT5_SERVER}"
            return 0
        fi
    fi

    log INFO "[mt5] Generating config for ${MT5_LOGIN}@${MT5_SERVER}..."
    mkdir -p "$MT5_CONFIG_DIR"

    cat > "$MT5_STARTUP_INI" << EOF
[Common]
Login=${MT5_LOGIN}
Password=${MT5_PASSWORD}
Server=${MT5_SERVER}
KeepPrivate=1
CertInstall=1
NewsEnable=1
ProxyEnable=0

[Experts]
AllowLiveTrading=1
AllowDllImport=1
Enabled=1
Account=0
Profile=0
EOF

    log INFO "[mt5] Config written to: $MT5_STARTUP_INI"
}

# ============================================================
# Main execution
# ============================================================
install_mt5_pip
install_mt5_terminal
generate_config
log INFO "[mt5] Setup complete"
