#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

PYTHON_INSTALLER="/tmp/python-installer.exe"

if ! "$wine_executable" python --version 2>/dev/null; then
    log INFO "[python-wine] Installing Python ${PYTHON_VERSION}..."

    # Get Python installer using prioritized cache
    get_file "python-installer.exe" "$python_url" "$PYTHON_INSTALLER"

    "$wine_executable" "$PYTHON_INSTALLER" /quiet InstallAllUsers=1 PrependPath=1
    rm -f "$PYTHON_INSTALLER"

    # Verify Python was installed
    if ! "$wine_executable" python --version 2>/dev/null; then
        log ERROR "[python-wine] Python installation failed"
        exit 1
    fi
    log INFO "[python-wine] Python installed successfully"
else
    log INFO "[python-wine] Python already installed"
fi

log INFO "[python-wine] Installing pip and libraries..."
if ! "$wine_executable" python -m pip install --upgrade --no-cache-dir pip; then
    log WARN "[python-wine] pip upgrade failed; continuing"
fi

# MetaTrader5 is REQUIRED for MT5 API
log INFO "[python-wine] Installing MetaTrader5==${MT5_PYPI_VERSION} (required)"
if ! is_wine_python_package_installed "MetaTrader5==${MT5_PYPI_VERSION}"; then
    if ! "$wine_executable" python -m pip install --no-cache-dir "MetaTrader5==${MT5_PYPI_VERSION}"; then
        log ERROR "[python-wine] MetaTrader5 install failed"
        exit 1
    fi
fi

# mt5linux is REQUIRED for RPyC server bridge
log INFO "[python-wine] Installing mt5linux and dependencies (required)"
if ! is_wine_python_package_installed "mt5linux"; then
    if ! "$wine_executable" python -m pip install --no-cache-dir --no-deps mt5linux; then
        log ERROR "[python-wine] mt5linux install failed"
        exit 1
    fi
    if ! "$wine_executable" python -m pip install --no-cache-dir "rpyc==5.3.1" "numpy<2" "plumbum==1.8.0"; then
        log ERROR "[python-wine] mt5linux dependencies install failed"
        exit 1
    fi
fi

# python-dateutil is REQUIRED for datetime handling
if ! is_wine_python_package_installed "python-dateutil"; then
    log INFO "[python-wine] Installing python-dateutil (required)"
    if ! "$wine_executable" python -m pip install --no-cache-dir python-dateutil; then
        log ERROR "[python-wine] python-dateutil install failed"
        exit 1
    fi
fi

# Verify critical packages can be imported
log INFO "[python-wine] Verifying package imports..."
if ! "$wine_executable" python -c "import MetaTrader5" 2>/dev/null; then
    log ERROR "[python-wine] MetaTrader5 import verification failed"
    exit 1
fi
if ! "$wine_executable" python -c "import rpyc" 2>/dev/null; then
    log ERROR "[python-wine] rpyc import verification failed"
    exit 1
fi
log INFO "[python-wine] All packages verified successfully"
