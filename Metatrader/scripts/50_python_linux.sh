#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# mt5linux GitHub repository
MT5LINUX_REPO="git+https://github.com/marlonsc/mt5linux.git@master"

log INFO "[8/9] Checking and installing mt5linux library in Linux"
if ! is_python_package_installed "mt5linux"; then
    log INFO "[8/9] Installing mt5linux from GitHub (marlonsc/mt5linux)"

    # Install dependencies first
    pip3 install --break-system-packages --no-cache-dir \
        "numpy>=2.1.0" "rpyc>=5.2.0" "plumbum>=1.8.0" "pyparsing>=3.0.0" || {
        log ERROR "[8/9] Failed to install mt5linux dependencies"
        exit 1
    }

    # Install mt5linux from GitHub
    pip3 install --break-system-packages --no-cache-dir "$MT5LINUX_REPO" || {
        log ERROR "[8/9] Failed to install mt5linux from GitHub"
        exit 1
    }

    # Verify installation
    MT5_VERSION=$(python3 -c "import mt5linux; print(getattr(mt5linux, '__version__', '0.2.1'))" 2>/dev/null || echo "unknown")
    log INFO "[8/9] mt5linux installed successfully (version: $MT5_VERSION)"
else
    MT5_VERSION=$(python3 -c "import mt5linux; print(getattr(mt5linux, '__version__', '0.2.1'))" 2>/dev/null || echo "unknown")
    log INFO "[8/9] mt5linux already installed (version: $MT5_VERSION)"
fi

log INFO "[8/9] Checking and installing pyxdg library in Linux"
if ! is_python_package_installed "pyxdg"; then
    log INFO "[8/9] Installing pyxdg"
    pip3 install --break-system-packages --no-cache-dir pyxdg || {
        log ERROR "[8/9] Failed to install pyxdg"
        exit 1
    }
else
    log INFO "[8/9] pyxdg already installed"
fi
