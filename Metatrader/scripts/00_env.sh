#!/bin/bash
set -euo pipefail

# ============================================================
# MT5 Docker - Shared Environment Variables and Functions
# ============================================================

# Core paths
export mt5file="${mt5file:-/config/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe}"
export WINEPREFIX="${WINEPREFIX:-/config/.wine}"
export WINEDEBUG="${WINEDEBUG:--all}"
# DLL overrides: disable Mono, use native ucrtbase for numpy 2.x (crealf fix)
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-mscoree=n,mscorlib=n,ucrtbase=n}"
export wine_executable="${wine_executable:-wine}"
export mt5server_port="${mt5server_port:-8001}"

# Cache and staging directories
export STAGING_DIR="${STAGING_DIR:-/opt/mt5-staging}"
export CACHE_DIR="${CACHE_DIR:-/cache}"

# Load version info from build-time manifest (if available)
if [ -f "$STAGING_DIR/.versions" ]; then
    # shellcheck source=/dev/null
    source "$STAGING_DIR/.versions"
fi

# ============================================================
# CENTRALIZED VERSION CONFIGURATION
# Single source of truth for ALL versions across scripts/modules
# ============================================================

# Core component versions
export PYTHON_VERSION="${PYTHON_VERSION:-3.13.11}"
export GECKO_VERSION="${GECKO_VERSION:-2.47.4}"
export MT5_PYPI_VERSION="${MT5_PYPI_VERSION:-5.0.5430}"

# Python module versions (Wine Python)
export RPYC_VERSION="${RPYC_VERSION:-6.0.2}"
export PYDANTIC_VERSION="${PYDANTIC_VERSION:-2.12}"
export PLUMBUM_VERSION="${PLUMBUM_VERSION:-1.8.0}"
export NUMPY_VERSION="${NUMPY_VERSION:-2.1}"

# mt5linux - always use main branch from GitHub (via tarball, not git+)
export MT5LINUX_REPO="${MT5LINUX_REPO:-https://github.com/marlonsc/mt5linux}"
export MT5LINUX_BRANCH="${MT5LINUX_BRANCH:-master}"

# pip install specifiers (derived from versions above)
export RPYC_SPEC="rpyc==${RPYC_VERSION}"
export PYDANTIC_SPEC="pydantic>=${PYDANTIC_VERSION},<3.0.0"
export PLUMBUM_SPEC="plumbum>=${PLUMBUM_VERSION}"
export NUMPY_SPEC="numpy>=${NUMPY_VERSION}"
# Use tarball URL (works without git installed in Wine)
export MT5LINUX_SPEC="${MT5LINUX_REPO}/archive/refs/heads/${MT5LINUX_BRANCH}.tar.gz"

# Construct URLs from versions
export python_url="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe"
export mt5setup_url="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

# Feature flags
export ENABLE_WIN_DOTNET="${ENABLE_WIN_DOTNET:-1}"

# Auto-login credentials (optional)
export MT5_LOGIN="${MT5_LOGIN:-}"
export MT5_PASSWORD="${MT5_PASSWORD:-}"
export MT5_SERVER="${MT5_SERVER:-}"

# Health monitoring and auto-recovery
export HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"
export AUTO_RECOVERY_ENABLED="${AUTO_RECOVERY_ENABLED:-1}"

# ============================================================
# Logging
# ============================================================
log() {
    local level="$1"; shift
    local msg="$*"
    printf '[%s] [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$msg"
}

# ============================================================
# get_file: Prioritized file retrieval with caching
# Priority: 1. External cache -> 2. Embedded staging -> 3. Download
# ============================================================
get_file() {
    local filename="$1"
    local url="$2"
    local dest="$3"

    # Ensure cache directory exists (non-critical, log if fails)
    if ! mkdir -p "$CACHE_DIR" 2>/dev/null; then
        log DEBUG "Cache dir unavailable: $CACHE_DIR"
    fi

    # Priority 1: External cache volume (survives prune)
    if [ -f "$CACHE_DIR/$filename" ]; then
        log INFO "Using cached: $filename (from cache volume)"
        cp "$CACHE_DIR/$filename" "$dest"
        return 0
    fi

    # Priority 2: Embedded staging (baked into image at build time)
    if [ -f "$STAGING_DIR/$filename" ]; then
        log INFO "Using staged: $filename (from image)"
        cp "$STAGING_DIR/$filename" "$dest"
        # Cache for next time (optional - log if fails)
        if cp "$STAGING_DIR/$filename" "$CACHE_DIR/$filename" 2>/dev/null; then
            log DEBUG "Cached staged file: $filename"
        fi
        return 0
    fi

    # Priority 3: Download (last resort)
    log INFO "Downloading: $filename from $url"
    if curl -fSL "$url" -o "$dest"; then
        # Cache for next time (optional - log if fails)
        if cp "$dest" "$CACHE_DIR/$filename" 2>/dev/null; then
            log INFO "Downloaded and cached: $filename"
        else
            log INFO "Downloaded: $filename (cache write skipped)"
        fi
        return 0
    else
        log ERROR "Failed to download: $filename from $url"
        return 1
    fi
}

# ============================================================
# Dependency checks
# ============================================================
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        log ERROR "$1 is not installed. Please install it to continue."
        exit 1
    fi
}

# Python package checks (Linux) - using importlib.metadata (Python 3.8+)
is_python_package_installed() {
    local pkg="$1"
    # Remove version specifiers for import check
    local pkg_name="${pkg%%[=<>]*}"
    python3 -c "from importlib.metadata import version; version('$pkg_name')" 2>/dev/null
    return $?
}

# Python package checks (Wine/Windows)
is_wine_python_package_installed() {
    local pkg="$1"
    # Remove version specifiers for import check
    local pkg_name="${pkg%%[=<>]*}"
    "$wine_executable" python -c "from importlib.metadata import version; version('$pkg_name')" 2>/dev/null
    return $?
}

# Verify core dependencies
check_dependency curl
check_dependency "$wine_executable"

# ============================================================
# Common paths
# ============================================================
export WINE_USER_DIR="$WINEPREFIX/drive_c/users/$(whoami)"
export DOCS_DIR="$WINE_USER_DIR/Documents"
export DEPS_MARKER="$WINEPREFIX/.deps-installed"
export PREFIX_CACHE_DIR="$WINEPREFIX/drive_c/.cache/wine"
export GECKO_MARKER="$WINEPREFIX/.gecko-installed"
export INIT_MARKER="$WINEPREFIX/.wine-init-done"
export MT5_LOGGED_IN_MARKER="$WINEPREFIX/.mt5-logged-in"

# MT5 configuration paths (consolidated here to avoid duplication)
export MT5_CONFIG_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/Config"
export MT5_STARTUP_INI="$MT5_CONFIG_DIR/startup.ini"

# Log versions on first load
if [ "${_ENV_LOADED:-}" != "1" ]; then
    log INFO "Versions: Python=${PYTHON_VERSION}, Gecko=${GECKO_VERSION}, MT5 PyPI=${MT5_PYPI_VERSION}"
    log INFO "Cache: STAGING_DIR=${STAGING_DIR}, CACHE_DIR=${CACHE_DIR}"
    export _ENV_LOADED=1
fi
