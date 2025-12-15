#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# mt5linux GitHub repository
MT5LINUX_REPO="git+https://github.com/marlonsc/mt5linux.git@master"

log INFO "[python-linux] Checking mt5linux library"

# Install from GitHub if not installed
if ! is_python_package_installed "mt5linux"; then
    log INFO "[python-linux] Installing mt5linux from GitHub"

    # Install dependencies first
    pip3 install --break-system-packages --no-cache-dir \
        "numpy>=2.1.0" "rpyc==6.0.2" "plumbum>=1.8.0" "pyparsing>=3.0.0" || {
        log ERROR "[python-linux] Failed to install dependencies"
        exit 1
    }

    # Install mt5linux from GitHub
    pip3 install --break-system-packages --no-cache-dir "$MT5LINUX_REPO" || {
        log ERROR "[python-linux] Failed to install mt5linux"
        exit 1
    }

    # Verify installation
    MT5_VERSION=$(python3 -c "import mt5linux; print(getattr(mt5linux, '__version__', '0.2.1'))" 2>/dev/null || echo "unknown")
    log INFO "[python-linux] mt5linux installed (version: $MT5_VERSION)"
else
    MT5_VERSION=$(python3 -c "import mt5linux; print(getattr(mt5linux, '__version__', '0.2.1'))" 2>/dev/null || echo "unknown")
    log INFO "[python-linux] mt5linux already installed (version: $MT5_VERSION)"
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
