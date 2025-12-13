#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

if ! "$wine_executable" python --version 2>/dev/null; then
    log INFO "[5/7] Installing Python in Wine..."
    curl -L "$python_url" -o /tmp/python-installer.exe
    "$wine_executable" /tmp/python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 || true
    rm -f /tmp/python-installer.exe
    log INFO "[5/7] Python installed in Wine."
else
    log INFO "[5/7] Python is already installed in Wine."
fi

log INFO "[6/7] Installing Python libraries"
"$wine_executable" python -m pip install --upgrade --no-cache-dir pip || true

log INFO "[6/7] Installing MetaTrader5 library in Windows"
if ! is_wine_python_package_installed "MetaTrader5==${metatrader_version}"; then
    "$wine_executable" python -m pip install --no-cache-dir "MetaTrader5==${metatrader_version}" || true
fi

log INFO "[6/7] Checking and installing mt5linux library in Windows if necessary"
if ! is_wine_python_package_installed "mt5linux"; then
    # Use local mt5linux installation for better compatibility
    "$wine_executable" python -m pip install --no-cache-dir --no-deps mt5linux || true
    "$wine_executable" python -m pip install --no-cache-dir rpyc plumbum numpy || true
fi

if ! is_wine_python_package_installed "python-dateutil"; then
    log INFO "[6/7] Installing python-dateutil library in Windows"
    "$wine_executable" python -m pip install --no-cache-dir python-dateutil || true
fi