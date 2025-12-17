#!/bin/bash
# MT5 Docker - Container Startup
# =============================================================================
# Orchestrates container initialization:
# 1. Exports all configuration (replaces 00_env.sh)
# 2. Runs setup.sh for Wine prefix + MT5 installation
# 3. Sets startup markers for s6-overlay coordination
# 4. Launches health monitor (optional)
# =============================================================================
set -euo pipefail

START_TS=$(date +%s)

# =============================================================================
# CONFIGURATION (centralized - previously in scripts/00_env.sh)
# =============================================================================

# Core directories
export STAGING_DIR="${STAGING_DIR:-/opt/mt5-staging}"
export CONFIG_DIR="${CONFIG_DIR:-/config}"
export CACHE_DIR="${CACHE_DIR:-/config/.cache}"
export WINE_PREFIX_TEMPLATE="${WINE_PREFIX_TEMPLATE:-/opt/wine-prefix-template}"

# Wine directories
export WINEPREFIX="${WINEPREFIX:-$CONFIG_DIR/.wine}"

# MT5 paths
export mt5file="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/terminal64.exe"
export MT5_CONFIG_DIR="$WINEPREFIX/drive_c/MT5Config"
export MT5_STARTUP_INI="$MT5_CONFIG_DIR/startup.ini"

# Wine configuration
export wine_executable="${wine_executable:-wine}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-winemenubuilder.exe,mscoree,mshtml=}"

# Wine Python path
export WINE_PYTHON_PATH="$WINEPREFIX/drive_c/Python/python.exe"

# RPyC server port
export mt5server_port="${mt5server_port:-8001}"

# Load versions from build manifest
if [ -f "$STAGING_DIR/.versions" ]; then
    source "$STAGING_DIR/.versions"
fi

# Version fallbacks (must match versions.env)
export PYTHON_VERSION="${PYTHON_VERSION:-3.12.8}"
export WINE_MONO_VERSION="${WINE_MONO_VERSION:-9.4.0}"
export GRPCIO_VERSION="${GRPCIO_VERSION:-1.76.0}"
export NUMPY_VERSION="${NUMPY_VERSION:-1.26.4}"

# Startup markers (used by s6-overlay svc-mt5server)
export STARTUP_MARKER="${STARTUP_MARKER:-/tmp/.mt5-startup-complete}"
export STARTUP_IN_PROGRESS="${STARTUP_IN_PROGRESS:-/tmp/.mt5-startup-in-progress}"

# Dependency marker (used by winetricks setup)
export DEPS_MARKER="$WINEPREFIX/.deps-installed"

# MT5 download URL (always latest)
export mt5setup_url="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

# Auto-login credentials (optional)
export MT5_LOGIN="${MT5_LOGIN:-}"
export MT5_PASSWORD="${MT5_PASSWORD:-}"
export MT5_SERVER="${MT5_SERVER:-}"

# =============================================================================
# LOGGING
# =============================================================================
log() {
    local level="$1"; shift
    printf '[%s] [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$*"
}
export -f log

# =============================================================================
# DEPENDENCY CHECKS
# =============================================================================
check_dependency() {
    command -v "$1" &>/dev/null || {
        log ERROR "$1 is not installed"
        exit 1
    }
}

check_dependency curl
check_dependency "$wine_executable"

# =============================================================================
# MAIN
# =============================================================================
log INFO "[startup] Starting MT5 Docker container..."
log INFO "[startup] Wine prefix: $WINEPREFIX"
log INFO "[startup] Wine Python: $WINE_PYTHON_PATH"

# Signal startup in progress (prevents race with svc-mt5server)
touch "$STARTUP_IN_PROGRESS"
rm -f "$STARTUP_MARKER"

# Run setup
SCRIPT_DIR="$(dirname "$0")"
if ! "$SCRIPT_DIR/setup.sh"; then
    log ERROR "[startup] Setup failed"
    rm -f "$STARTUP_IN_PROGRESS"
    exit 1
fi

# Signal startup complete
touch "$STARTUP_MARKER"
rm -f "$STARTUP_IN_PROGRESS"

END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))
log INFO "[startup] MT5 setup completed in ${ELAPSED}s"

# Launch health monitor in background (optional)
if [ "${AUTO_RECOVERY_ENABLED:-1}" = "1" ]; then
    log INFO "[startup] Starting health monitor..."
    "$SCRIPT_DIR/health_monitor.sh" --daemon &
fi
