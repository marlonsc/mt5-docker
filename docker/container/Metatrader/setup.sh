#!/bin/bash
# MT5 Docker - Setup Script
# =============================================================================
# Consolidates all setup operations (previously in scripts/ folder):
# 1. Config unpack (from 05_config_unpack.sh)
# 2. Wine prefix init (from 10_prefix_init.sh)
# 3. Winetricks deps (from 20_winetricks.sh)
# 4. MT5 installation (from 30_mt5.sh)
# 5. Bridge copy (from 50_copy_bridge.sh)
#
# Environment variables are inherited from start.sh (must be exported)
# =============================================================================
set -euo pipefail

# Installer timeout - enough time for full installation
MT5_INSTALL_TIMEOUT=120

# =============================================================================
# LOGGING (inherited from start.sh, but define fallback)
# =============================================================================
if ! declare -f log > /dev/null 2>&1; then
    log() {
        local level="$1"; shift
        printf '[%s] [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$*"
    }
fi

# =============================================================================
# 1. CONFIG UNPACK (from 05_config_unpack.sh)
# =============================================================================
unpack_config() {
    local archive="$CONFIG_DIR/mt5-config.tar.gz"

    if [ ! -f "$archive" ]; then
        log INFO "[setup] No config archive to unpack"
        return 0
    fi

    log INFO "[setup] Unpacking config archive..."
    tar -xzf "$archive" -C "$CONFIG_DIR"
    rm -f "$archive"
    log INFO "[setup] Config unpacked"
}

# =============================================================================
# 2. WINE PREFIX INIT (from 10_prefix_init.sh)
# =============================================================================
init_wine_prefix() {
    if [ -d "$WINEPREFIX/drive_c" ]; then
        log INFO "[setup] Wine prefix already exists: $WINEPREFIX"
        return 0
    fi

    if [ ! -d "$WINE_PREFIX_TEMPLATE/drive_c" ]; then
        log ERROR "[setup] FATAL: Wine prefix template not found: $WINE_PREFIX_TEMPLATE"
        return 1
    fi

    log INFO "[setup] Initializing Wine prefix from template..."
    mkdir -p "$(dirname "$WINEPREFIX")"
    cp -a "$WINE_PREFIX_TEMPLATE" "$WINEPREFIX"
    chown -R abc:abc "$WINEPREFIX"
    log INFO "[setup] Wine prefix initialized: $WINEPREFIX"
}

# =============================================================================
# 3. WINETRICKS DEPS (from 20_winetricks.sh)
# =============================================================================
install_winetricks_deps() {
    if [ -f "$DEPS_MARKER" ]; then
        log INFO "[setup] Winetricks deps already installed"
        return 0
    fi

    log INFO "[setup] Installing winetricks dependencies..."
    export WINEDLLOVERRIDES="winemenubuilder.exe,mscoree,mshtml="
    export WINETRICKS_UNATTENDED=1
    export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/.cache}"
    export W_CACHE="${W_CACHE:-/tmp/.cache/winetricks}"
    mkdir -p "$W_CACHE"

    # vcrun2019 (recommended for MT5)
    log INFO "[setup] Installing vcrun2019..."
    xvfb-run sh -c "winetricks -q vcrun2019; wineserver -w" || \
        log WARN "[setup] vcrun2019 failed (non-critical)"

    # Restore win10 version (winetricks may reset to winxp)
    log INFO "[setup] Setting Windows version to win10..."
    xvfb-run sh -c "winetricks -q win10; wineserver -w" || \
        log WARN "[setup] win10 failed (non-critical)"

    # Cleanup cache
    rm -rf "$W_CACHE"/*

    touch "$DEPS_MARKER"
    log INFO "[setup] Winetricks deps installed"
}

# =============================================================================
# 4. MT5 INSTALLATION (from 30_mt5.sh)
# =============================================================================
install_mt5_pip() {
    if [ ! -f "$WINE_PYTHON_PATH" ]; then
        log ERROR "[setup] FATAL: Wine Python not found at $WINE_PYTHON_PATH"
        return 1
    fi

    log INFO "[setup] Installing MetaTrader5 pip package..."

    # Build pip install arguments based on MT5_UPDATE setting
    local pip_args="--no-deps"
    if [ "${MT5_UPDATE:-1}" = "1" ]; then
        pip_args="--upgrade --no-cache-dir ${pip_args}"
        log INFO "[setup] Installing MetaTrader5 (update enabled, fresh install)..."
    else
        log INFO "[setup] Installing MetaTrader5 (update disabled, using cached)..."
    fi

    "$wine_executable" "$WINE_PYTHON_PATH" -m pip install ${pip_args} \
        MetaTrader5 2>&1 || {
        log ERROR "[setup] MetaTrader5 installation failed"
        return 1
    }

    # Verify imports work
    log INFO "[setup] Verifying package imports..."
    "$wine_executable" "$WINE_PYTHON_PATH" -c "
import MetaTrader5
import rpyc
import numpy
print(f'MetaTrader5 {MetaTrader5.__version__}')
print(f'rpyc {rpyc.__version__}')
print(f'numpy {numpy.__version__}')
" 2>/dev/null || {
        log ERROR "[setup] Package verification failed"
        return 1
    }

    log INFO "[setup] MetaTrader5 pip package installed"
}

install_mt5_terminal() {
    if [ -e "$mt5file" ]; then
        log INFO "[setup] MT5 terminal already installed: $mt5file"
        return 0
    fi

    log INFO "[setup] Installing MetaTrader 5 terminal..."

    local MT5_SETUP="/tmp/mt5setup.exe"

    # Download installer
    log INFO "[setup] Downloading mt5setup.exe..."
    curl -fSL -o "$MT5_SETUP" "$mt5setup_url" || {
        log ERROR "[setup] Failed to download mt5setup.exe"
        return 1
    }

    # Run installer with timeout - let it complete naturally
    log INFO "[setup] Running installer (timeout: ${MT5_INSTALL_TIMEOUT}s)..."
    "$wine_executable" "$MT5_SETUP" "/auto" &
    local INSTALLER_PID=$!

    local elapsed=0
    while [ $elapsed -lt $MT5_INSTALL_TIMEOUT ]; do
        if ! kill -0 $INSTALLER_PID 2>/dev/null; then
            log INFO "[setup] Installer process completed"
            break
        fi

        # Check for terminal but don't kill installer - let it finish
        if [ -e "$mt5file" ] && [ $((elapsed % 10)) -eq 0 ]; then
            log INFO "[setup] Terminal detected, waiting for installer to finish..."
        fi

        sleep 5
        elapsed=$((elapsed + 5))
    done

    # Timeout handling
    if kill -0 $INSTALLER_PID 2>/dev/null; then
        log WARN "[setup] Installer timeout after ${MT5_INSTALL_TIMEOUT}s - forcing kill"
        kill $INSTALLER_PID 2>/dev/null || true
        pkill -f "mt5setup" 2>/dev/null || true
        sleep 2
    fi

    rm -f "$MT5_SETUP"

    # Verify installation
    if [ ! -e "$mt5file" ]; then
        log ERROR "[setup] MT5 terminal installation failed - executable not found"
        return 1
    fi

    log INFO "[setup] MT5 terminal installed: $mt5file"

    # Kill any terminal process started by installer
    # (svc-mt5server will start it properly later)
    if pgrep -f "terminal64.exe" > /dev/null 2>&1; then
        log INFO "[setup] Stopping terminal process started by installer..."
        pkill -f "terminal64.exe" 2>/dev/null || true
        sleep 2
        # Force kill if still running
        pkill -9 -f "terminal64.exe" 2>/dev/null || true
    fi

    # Clean up wine server to ensure fresh state
    wineserver -k 2>/dev/null || true
    sleep 1

    log INFO "[setup] Installation cleanup complete"
}

generate_mt5_config() {
    if [ -z "${MT5_LOGIN:-}" ] || [ -z "${MT5_PASSWORD:-}" ] || [ -z "${MT5_SERVER:-}" ]; then
        log INFO "[setup] No MT5 credentials provided, skipping config"
        return 0
    fi

    # Skip if config already exists with same credentials
    if [ -f "$MT5_STARTUP_INI" ]; then
        if grep -q "Login=${MT5_LOGIN}" "$MT5_STARTUP_INI" 2>/dev/null; then
            log INFO "[setup] MT5 config already exists for ${MT5_LOGIN}@${MT5_SERVER}"
            return 0
        fi
    fi

    log INFO "[setup] Generating MT5 config for ${MT5_LOGIN}@${MT5_SERVER}..."
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

    log INFO "[setup] MT5 config written to: $MT5_STARTUP_INI"
}

# =============================================================================
# 5. BRIDGE COPY (from 50_copy_bridge.sh)
# =============================================================================
copy_bridge() {
    local BRIDGE_SOURCE="/Metatrader/bridge.py"
    local SITE_PACKAGES="$WINEPREFIX/drive_c/Python/Lib/site-packages"
    local TARGET_DIR="$SITE_PACKAGES/mt5linux"

    if [ ! -f "$BRIDGE_SOURCE" ]; then
        log ERROR "[setup] FATAL: bridge.py not found at $BRIDGE_SOURCE"
        return 1
    fi

    if [ ! -d "$SITE_PACKAGES" ]; then
        log ERROR "[setup] FATAL: Wine Python site-packages not found at $SITE_PACKAGES"
        return 1
    fi

    log INFO "[setup] Copying bridge.py to Wine Python..."

    # Create mt5linux package directory
    mkdir -p "$TARGET_DIR"

    # Copy bridge.py
    cp "$BRIDGE_SOURCE" "$TARGET_DIR/bridge.py"

    # Create __init__.py if missing
    if [ ! -f "$TARGET_DIR/__init__.py" ]; then
        echo '"""mt5linux bridge module."""' > "$TARGET_DIR/__init__.py"
    fi

    # Create __main__.py for -m execution
    cat > "$TARGET_DIR/__main__.py" << 'EOF'
"""Allow running as python -m mt5linux.bridge"""
from .bridge import main

if __name__ == "__main__":
    main()
EOF

    log INFO "[setup] bridge.py copied to: $TARGET_DIR"
}

# =============================================================================
# MAIN SETUP SEQUENCE
# =============================================================================
log INFO "[setup] Starting MT5 Docker setup..."

unpack_config
init_wine_prefix
install_winetricks_deps
install_mt5_pip
install_mt5_terminal
generate_mt5_config
copy_bridge

log INFO "[setup] Setup complete"
