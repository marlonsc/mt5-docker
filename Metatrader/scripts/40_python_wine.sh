#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

PYTHON_INSTALLER="/tmp/python-installer.exe"

if ! "$wine_executable" python --version 2>/dev/null; then
    log INFO "[7/9] Installing Python ${PYTHON_VERSION} in Wine..."

    # Get Python installer using prioritized cache
    get_file "python-installer.exe" "$python_url" "$PYTHON_INSTALLER"

    "$wine_executable" "$PYTHON_INSTALLER" /quiet InstallAllUsers=1 PrependPath=1 || true
    rm -f "$PYTHON_INSTALLER"
    log INFO "[7/9] Python installed in Wine."
else
    log INFO "[7/9] Python is already installed in Wine."
fi

log INFO "[7/9] Installing Python libraries in Wine"
"$wine_executable" python -m pip install --upgrade --no-cache-dir pip || true

log INFO "[7/9] Installing MetaTrader5 library (version: ${MT5_PYPI_VERSION})"
if ! is_wine_python_package_installed "MetaTrader5==${MT5_PYPI_VERSION}"; then
    "$wine_executable" python -m pip install --no-cache-dir "MetaTrader5==${MT5_PYPI_VERSION}" || true
fi

log INFO "[7/9] Checking and installing mt5linux library in Windows if necessary"
if ! is_wine_python_package_installed "mt5linux"; then
    "$wine_executable" python -m pip install --no-cache-dir --no-deps mt5linux || true
    "$wine_executable" python -m pip install --no-cache-dir "rpyc==5.3.1" "numpy<2" "plumbum==1.8.0" || true
fi

if ! is_wine_python_package_installed "python-dateutil"; then
    log INFO "[7/9] Installing python-dateutil library in Windows"
    "$wine_executable" python -m pip install --no-cache-dir python-dateutil || true
fi
