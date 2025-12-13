#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[7/11] Checking and installing mt5linux library in Linux"
if ! is_python_package_installed "mt5linux"; then
    log INFO "[7/11] Installing mt5linux and dependencies"
    pip3 install --break-system-packages --no-cache-dir --no-deps mt5linux && \
    pip3 install --break-system-packages --no-cache-dir rpyc plumbum numpy || {
        log ERROR "[7/11] Failed to install mt5linux dependencies"
        exit 1
    }
else
    log INFO "[7/11] mt5linux already installed"
fi

log INFO "[8/11] Checking and installing pyxdg library in Linux"
if ! is_python_package_installed "pyxdg"; then
    log INFO "[8/11] Installing pyxdg"
    pip3 install --break-system-packages --no-cache-dir pyxdg || {
        log ERROR "[8/11] Failed to install pyxdg"
        exit 1
    }
else
    log INFO "[8/11] pyxdg already installed"
fi