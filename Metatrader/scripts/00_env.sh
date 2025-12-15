#!/bin/bash
set -euo pipefail

# ============================================================
# MT5 Docker - Shared Environment Variables
# ============================================================

# Core directories
export STAGING_DIR="${STAGING_DIR:-/opt/mt5-staging}"
export CONFIG_DIR="${CONFIG_DIR:-/config}"
export CACHE_DIR="${CACHE_DIR:-/config/.cache}"
export WINE_PREFIX_TEMPLATE="${WINE_PREFIX_TEMPLATE:-/opt/wine-prefix-template}"

# Wine directories
export WINEPREFIX="${WINEPREFIX:-$CONFIG_DIR/.wine}"

# MT5 paths
export mt5file="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/terminal64.exe"
# Config in path WITHOUT spaces to avoid shell quoting issues with /config: argument
export MT5_CONFIG_DIR="$WINEPREFIX/drive_c/MT5Config"
export MT5_STARTUP_INI="$MT5_CONFIG_DIR/startup.ini"

# Wine configuration
export wine_executable="${wine_executable:-wine}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-winemenubuilder.exe,mscoree,mshtml=}"

# Wine Python path (installed at C:\Python during build)
export WINE_PYTHON_PATH="$WINEPREFIX/drive_c/Python/python.exe"

# RPyC server port
export mt5server_port="${mt5server_port:-8001}"

# Load versions from build manifest
if [ -f "$STAGING_DIR/.versions" ]; then
    source "$STAGING_DIR/.versions"
fi

# Version defaults (if not in manifest)
export PYTHON_VERSION="${PYTHON_VERSION:-3.13.11}"
export GECKO_VERSION="${GECKO_VERSION:-2.47.4}"

# MT5 download URL (always latest)
export mt5setup_url="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

# Auto-login credentials (optional)
export MT5_LOGIN="${MT5_LOGIN:-}"
export MT5_PASSWORD="${MT5_PASSWORD:-}"
export MT5_SERVER="${MT5_SERVER:-}"

# Markers
export INIT_MARKER="$WINEPREFIX/.wine-init-done"
export DEPS_MARKER="$WINEPREFIX/.deps-installed"

# ============================================================
# Logging
# ============================================================
log() {
    local level="$1"; shift
    printf '[%s] [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$*"
}

# ============================================================
# Dependency checks
# ============================================================
check_dependency() {
    command -v "$1" &>/dev/null || {
        log ERROR "$1 is not installed"
        exit 1
    }
}

check_dependency curl
check_dependency "$wine_executable"

# Log on first load
if [ "${_ENV_LOADED:-}" != "1" ]; then
    log INFO "Wine prefix: $WINEPREFIX"
    log INFO "Wine Python: $WINE_PYTHON_PATH"
    export _ENV_LOADED=1
fi
