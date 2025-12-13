#!/bin/bash
set -euo pipefail

# Shared environment variables
export mt5file="${mt5file:-/config/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe}"
export WINEPREFIX="${WINEPREFIX:-/config/.wine}"
export WINEDEBUG="${WINEDEBUG:--all}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-mscoree=n,mscorlib=n}"
export wine_executable="${wine_executable:-wine}"
export metatrader_version="${metatrader_version:-5.0.4993}"
export mt5server_port="${mt5server_port:-8001}"
export python_url="${python_url:-https://www.python.org/ftp/python/3.13.10/python-3.13.10-amd64.exe}"
export mt5setup_url="${mt5setup_url:-https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe}"

# Structured logging with timestamp and level
log() {
    local level="$1"; shift
    local msg="$*"
    printf '[%s] [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$msg"
}

# Function to check if a dependency is installed
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        log ERROR "$1 is not installed. Please install it to continue."
        exit 1
    fi
}

# Python package checks (Linux)
is_python_package_installed() {
    python3 -c "import pkg_resources; exit(not pkg_resources.require('$1'))" 2>/dev/null
    return $?
}

# Python package checks (Wine/Windows)
is_wine_python_package_installed() {
    "$wine_executable" python -c "import pkg_resources; exit(not pkg_resources.require('$1'))" 2>/dev/null
    return $?
}

# Verify core dependencies once here
check_dependency curl
check_dependency "$wine_executable"

# Common paths exported for other scripts
export WINE_USER_DIR="$WINEPREFIX/drive_c/users/$(whoami)"
export DOCS_DIR="$WINE_USER_DIR/Documents"
export DEPS_MARKER="$WINEPREFIX/.deps-installed"
export PREFIX_CACHE_DIR="$WINEPREFIX/drive_c/.cache/wine"
export MONO_MSI="$PREFIX_CACHE_DIR/wine-mono-10.3.0-x86.msi"
export GECKO_X64="$PREFIX_CACHE_DIR/wine-gecko-2.47.4-x86_64.msi"
export GECKO_X86="$PREFIX_CACHE_DIR/wine-gecko-2.47.4-x86.msi"
export MONO_MARKER="$WINEPREFIX/.mono-installed"
export GECKO_MARKER="$WINEPREFIX/.gecko-installed"