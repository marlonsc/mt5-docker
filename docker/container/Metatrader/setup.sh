#!/bin/bash
# MT5 Docker - Setup Script
# =============================================================================
# Consolidates all setup operations (previously in scripts/ folder):
# 1. Config unpack (from 05_config_unpack.sh)
# 2. Wine prefix init (from 10_prefix_init.sh)
# 3. Wine configuration (simplified - no winetricks needed)
# 4. MT5 installation (from 30_mt5.sh)
# 5. Bridge copy (from 50_copy_bridge.sh)
#
# Note: Win10 is set at build time. Wine Mono provides .NET support.
# No winetricks required (following original gmag11/MetaTrader5-Docker-Image).
#
# Environment variables are inherited from start.sh (must be exported)
# =============================================================================
set -euo pipefail

# Installer timeout - enough time for full installation (5 minutes)
MT5_INSTALL_TIMEOUT=300

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
# RETRY HELPER
# =============================================================================
retry_with_backoff() {
    local max_attempts=$1
    local func_name=$2
    local attempt=1
    local delay=5

    while [ $attempt -le $max_attempts ]; do
        log INFO "[setup] Attempt $attempt/$max_attempts: $func_name"
        if "$func_name"; then
            log INFO "[setup] $func_name succeeded on attempt $attempt"
            return 0
        fi
        if [ $attempt -lt $max_attempts ]; then
            log WARN "[setup] $func_name failed (attempt $attempt/$max_attempts), retrying in ${delay}s..."
            sleep $delay
            delay=$((delay * 2))
        fi
        attempt=$((attempt + 1))
    done

    log ERROR "[setup] $func_name failed after $max_attempts attempts"
    return 1
}

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
# 3. WINE CONFIGURATION (simplified - no winetricks needed)
# Win10 is set during build; Wine Mono provides .NET support
# =============================================================================
configure_wine_settings() {
    if [ -f "$DEPS_MARKER" ]; then
        log INFO "[setup] Wine already configured"
        return 0
    fi

    log INFO "[setup] Configuring Wine settings..."

    # Verify Windows version is set to win10 (done at build time)
    # If not, set it via registry (no winetricks needed)
    if ! wine reg query 'HKEY_CURRENT_USER\Software\Wine' /v Version 2>/dev/null | grep -q "win10"; then
        log INFO "[setup] Setting Windows version to win10..."
        wine reg add 'HKEY_CURRENT_USER\Software\Wine' /v Version /t REG_SZ /d 'win10' /f 2>/dev/null || \
            log WARN "[setup] Failed to set win10 (non-critical)"
        wineserver -w 2>/dev/null || true
    else
        log INFO "[setup] Windows version already set to win10"
    fi

    touch "$DEPS_MARKER"
    log INFO "[setup] Wine configured"
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
import grpc
import numpy
print(f'MetaTrader5 {MetaTrader5.__version__}')
print(f'grpcio {grpc.__version__}')
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

    # Run installer with timeout
    log INFO "[setup] Running installer (timeout: ${MT5_INSTALL_TIMEOUT}s)..."
    "$wine_executable" "$MT5_SETUP" "/auto" &
    local INSTALLER_PID=$!

    local elapsed=0
    local terminal_detected=0
    while [ $elapsed -lt $MT5_INSTALL_TIMEOUT ]; do
        if ! kill -0 $INSTALLER_PID 2>/dev/null; then
            log INFO "[setup] Installer process completed"
            break
        fi

        # Check for terminal - when detected, wait 10s then proceed
        if [ -e "$mt5file" ]; then
            if [ $terminal_detected -eq 0 ]; then
                log INFO "[setup] Terminal detected! Waiting 10s for installer to stabilize..."
                terminal_detected=1
                sleep 10
                log INFO "[setup] Killing installer and proceeding..."
                kill $INSTALLER_PID 2>/dev/null || true
                pkill -f "mt5setup" 2>/dev/null || true
                sleep 2
                break
            fi
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
# 5. BRIDGE COPY (gRPC bridge + proto files)
# =============================================================================
copy_bridge() {
    local METATRADER_DIR="/Metatrader"
    local SITE_PACKAGES="$WINEPREFIX/drive_c/Python/Lib/site-packages"
    local TARGET_DIR="$SITE_PACKAGES/mt5linux"

    # Required files for gRPC bridge
    local REQUIRED_FILES="bridge.py mt5_pb2.py mt5_pb2_grpc.py"

    for file in $REQUIRED_FILES; do
        if [ ! -f "$METATRADER_DIR/$file" ]; then
            log ERROR "[setup] FATAL: $file not found at $METATRADER_DIR/$file"
            return 1
        fi
    done

    if [ ! -d "$SITE_PACKAGES" ]; then
        log ERROR "[setup] FATAL: Wine Python site-packages not found at $SITE_PACKAGES"
        return 1
    fi

    log INFO "[setup] Copying gRPC bridge files to Wine Python..."

    # Create mt5linux package directory
    mkdir -p "$TARGET_DIR"

    # Copy all bridge files
    for file in $REQUIRED_FILES; do
        cp "$METATRADER_DIR/$file" "$TARGET_DIR/$file"
        log INFO "[setup] Copied $file"
    done

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

    log INFO "[setup] gRPC bridge files copied to: $TARGET_DIR"
}

# =============================================================================
# MAIN SETUP SEQUENCE
# =============================================================================
log INFO "[setup] Starting MT5 Docker setup..."

# Non-critical steps (no retry needed)
unpack_config
init_wine_prefix
configure_wine_settings

# Critical steps with retry
if ! retry_with_backoff 3 install_mt5_pip; then
    log ERROR "[setup] FATAL: Could not install MT5 pip package after retries"
    exit 1
fi

if ! retry_with_backoff 2 install_mt5_terminal; then
    log ERROR "[setup] FATAL: Could not install MT5 terminal after retries"
    exit 1
fi

# Non-critical steps
generate_mt5_config
copy_bridge

log INFO "[setup] Setup complete"
