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
    # Idempotency keys on the .build-complete marker (written only at the very end
    # of a successful build), NOT on drive_c: drive_c is created early, so a
    # container killed mid-build (OOM/SIGKILL, before the failure cleanup runs)
    # would otherwise leave a broken prefix that the old guard never rebuilt.
    if [ -f "$WINEPREFIX/.build-complete" ]; then
        log INFO "[setup] Wine prefix already built: $WINEPREFIX"
        return 0
    fi
    if [ -d "$WINEPREFIX" ]; then
        log WARN "[setup] Incomplete Wine prefix found (no .build-complete); rebuilding from scratch"
        rm -rf "$WINEPREFIX"
    fi

    # First boot: build the Wine prefix (Mono + Gecko + Python + gRPC packages)
    # HERE, in this single isolated container. A former build-time `wine-builder`
    # BuildKit stage did this, but its Xvfb/wineserver/msiexec sequence raced
    # against BuildKit's concurrent stage scheduling and failed Gecko msiexec
    # nondeterministically (exit 91 / "X connection broken"). The identical steps
    # run reliably in a single container (== this first boot), and the result
    # persists to the /config volume so restarts are idempotent.
    log INFO "[setup] Building Wine prefix at first boot (one-time, ~3-5 min)..."

    local staging="${STAGING_DIR:-/opt/mt5-staging}"
    local mono_msi gecko64_msi gecko32_msi py_exe
    mono_msi=$(ls "$staging"/wine-mono-*-x86.msi 2>/dev/null | head -1) || true
    gecko64_msi=$(ls "$staging"/wine-gecko-*-x86_64.msi 2>/dev/null | head -1) || true
    gecko32_msi=$(ls "$staging"/wine-gecko-*-x86.msi 2>/dev/null | head -1) || true
    py_exe="$staging/python-installer.exe"
    local f
    for f in "$mono_msi" "$gecko64_msi" "$gecko32_msi" "$py_exe"; do
        if [ -z "$f" ] || [ ! -f "$f" ]; then
            log ERROR "[setup] FATAL: Wine prefix installer missing under $staging (resolved: '$f')"
            return 1
        fi
    done

    # Dedicated headless X for the install: matches the proven build environment
    # and is independent of the KasmVNC desktop X. Poll readiness (xdpyinfo from
    # x11-utils) instead of a blind sleep.
    local wb_display=":99"
    local rc=0
    Xvfb "$wb_display" -screen 0 1280x1024x24 -nolisten tcp &
    local xvfb_pid=$!
    local waited=0
    while [ $waited -lt 15 ] && ! DISPLAY="$wb_display" xdpyinfo >/dev/null 2>&1; do
        sleep 1
        waited=$((waited + 1))
    done
    if ! DISPLAY="$wb_display" xdpyinfo >/dev/null 2>&1; then
        log ERROR "[setup] FATAL: Xvfb did not become ready on $wb_display"
        kill "$xvfb_pid" 2>/dev/null || true
        return 1
    fi

    # Isolated env block so build-only overrides never leak to later steps.
    (
        set -e
        export DISPLAY="$wb_display"
        export WINEARCH=win64
        export WINEPREFIX
        export WINEDEBUG=-all
        export WINEDLLOVERRIDES="winemenubuilder.exe=d;mscoree=d"
        mkdir -p "$WINEPREFIX"

        log INFO "[setup] [prefix 1/6] Initializing Wine prefix..."
        wine reg add 'HKCU\Software\Wine\DllOverrides' /v winemenubuilder.exe /t REG_SZ /d '' /f
        wine reg add 'HKCU\Software\Wine\DllOverrides' /v mscoree /t REG_SZ /d '' /f
        wineserver -w
        test -d "$WINEPREFIX/drive_c"

        log INFO "[setup] [prefix 2/6] Installing Wine Mono..."
        wine msiexec /i "$mono_msi" /quiet
        wineserver -w

        log INFO "[setup] [prefix 3/6] Installing Wine Gecko (x86_64 + x86)..."
        wine msiexec /i "$gecko64_msi" /quiet
        wine msiexec /i "$gecko32_msi" /quiet
        wineserver -w

        log INFO "[setup] [prefix 4/6] Setting Windows version to win10..."
        wine reg add 'HKEY_CURRENT_USER\Software\Wine' /v Version /t REG_SZ /d 'win10' /f
        wineserver -w

        log INFO "[setup] [prefix 5/6] Installing Python (Wine side)..."
        wine "$py_exe" /quiet TargetDir='C:\Python' Include_doc=0 InstallAllUsers=1 PrependPath=1 Include_pip=1
        wineserver -w
        test -f "$WINE_PYTHON_PATH"
        wine "$WINE_PYTHON_PATH" --version
        wineserver -w

        log INFO "[setup] [prefix 6/6] Installing gRPC bridge packages..."
        wine "$WINE_PYTHON_PATH" -m pip install --upgrade --no-cache-dir pip
        # protobuf floor MUST match the gencode version baked into mt5_pb2.py
        # (ValidateProtobufRuntimeVersion(... 6, 31, 1 ...)). A runtime OLDER than
        # the gencode raises protobuf.runtime_version.VersionError at import and the
        # bridge crashes on startup (never binds the port -> client hangs). Keep this
        # floor == PROTOBUF_VERSION in versions.env whenever the stubs are regenerated.
        wine "$WINE_PYTHON_PATH" -m pip install --no-cache-dir --only-binary :all: \
            "grpcio>=${GRPCIO_VERSION:-1.76.0},<2.0" \
            "protobuf>=${PROTOBUF_VERSION:-6.31.1},<7.0" \
            "numpy==${NUMPY_VERSION:-1.26.4}" \
            "orjson>=3.9.0"
        wineserver -w
        wineserver -k 2>/dev/null || true
    ) || rc=$?

    kill "$xvfb_pid" 2>/dev/null || true

    if [ $rc -ne 0 ]; then
        # Remove the half-built prefix so the idempotency check above does not
        # skip a clean rebuild on the next attempt (no hidden partial state).
        rm -rf "$WINEPREFIX" 2>/dev/null || true
        log ERROR "[setup] FATAL: Wine prefix build failed (rc=$rc)"
        return 1
    fi

    touch "$WINEPREFIX/.build-complete"
    log INFO "[setup] Wine prefix built and ready: $WINEPREFIX"
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
        "MetaTrader5==${MT5_PYPI_VERSION:-5.0.5735}" 2>&1 || {
        log ERROR "[setup] MetaTrader5 installation failed"
        return 1
    }

    # Verify imports work
    log INFO "[setup] Verifying package imports..."
    "$wine_executable" "$WINE_PYTHON_PATH" -c "
import MetaTrader5
import grpc
import numpy
import google.protobuf
print(f'MetaTrader5 {MetaTrader5.__version__}')
print(f'grpcio {grpc.__version__}')
print(f'protobuf {google.protobuf.__version__}')
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

    # Fail loud at build time if the protobuf RUNTIME is older than the gencode
    # baked into mt5_pb2.py. This is the exact import the bridge does on startup;
    # catching it here turns a silent crash-loop (bridge never binds 8001 -> client
    # hangs ~90s) into a build-time FATAL with a clear message.
    if ! "$wine_executable" "$WINE_PYTHON_PATH" -c "from mt5linux import mt5_pb2, mt5_pb2_grpc" 2>&1; then
        log ERROR "[setup] FATAL: bridge stubs fail to import -- protobuf runtime/gencode mismatch?"
        log ERROR "[setup]        check 'protobuf>=PROTOBUF_VERSION' in setup.sh matches mt5_pb2.py gencode"
        return 1
    fi

    log INFO "[setup] gRPC bridge files copied to: $TARGET_DIR"
}

# =============================================================================
# MAIN SETUP SEQUENCE
# =============================================================================
log INFO "[setup] Starting MT5 Docker setup..."

# Non-critical steps (no retry needed)
unpack_config

# First-boot Wine prefix build (critical). Retried: init_wine_prefix removes any
# half-built prefix on failure, so a retry rebuilds cleanly (no hidden state).
if ! retry_with_backoff 2 init_wine_prefix; then
    log ERROR "[setup] FATAL: Could not build Wine prefix after retries"
    exit 1
fi

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
