#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# mt5linux - ALWAYS pull from main branch (force reinstall)
# Uses tarball URL to avoid git dependency and ensure fresh download
log INFO "[python-linux] Installing mt5linux from GitHub (${MT5LINUX_REPO}@${MT5LINUX_BRANCH})"

# Install dependencies first
pip3 install --break-system-packages --no-cache-dir \
    "numpy>=2.1.0" "rpyc>=6.0.0" "plumbum>=1.8.0" "pyparsing>=3.0.0" "structlog>=25.0.0" || {
    log ERROR "[python-linux] Failed to install dependencies"
    exit 1
}

# Install mt5linux from GitHub (ALWAYS force reinstall to get latest)
pip3 install --break-system-packages --no-cache-dir --force-reinstall --no-deps "${MT5LINUX_SPEC}" || {
    log ERROR "[python-linux] Failed to install mt5linux"
    exit 1
}

# Verify installation
MT5_VERSION=$(python3 -c "import mt5linux; print(getattr(mt5linux, '__version__', '0.2.1'))" 2>/dev/null || echo "unknown")
log INFO "[python-linux] mt5linux installed (version: $MT5_VERSION)"

# Verify imports work
log INFO "[python-linux] Verifying mt5linux imports..."
if ! python3 -c "from mt5linux import MetaTrader5; print('MetaTrader5 client available')" 2>/dev/null; then
    log ERROR "[python-linux] mt5linux import verification failed"
    exit 1
fi

log INFO "[python-linux] Checking pyxdg library"
if ! is_python_package_installed "pyxdg"; then
    log INFO "[python-linux] Installing pyxdg"
    pip3 install --break-system-packages --no-cache-dir pyxdg || {
        log ERROR "[python-linux] Failed to install pyxdg"
        exit 1
    }
else
    log INFO "[python-linux] pyxdg already installed"
fi
