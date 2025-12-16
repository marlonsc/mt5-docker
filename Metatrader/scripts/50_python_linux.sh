#!/bin/bash
# Install and verify Linux Python packages at RUNTIME
# mt5linux is installed here (not in Dockerfile) to always get latest version
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[python-linux] Setting up Linux Python packages..."

# Install mt5linux from GitHub (latest version)
# Base packages (numpy, rpyc, plumbum) are pre-installed in Dockerfile
log INFO "[python-linux] Installing mt5linux bridge package (latest)..."
python3 -m pip install --break-system-packages --upgrade --no-cache-dir --ignore-requires-python \
    'https://github.com/marlonsc/mt5linux/archive/refs/heads/master.tar.gz' 2>&1 || {
    log ERROR "[python-linux] FATAL: mt5linux installation failed"
    exit 1
}

# Verify all packages
log INFO "[python-linux] Verifying Linux Python packages..."
python3 -c "from mt5linux import MetaTrader5; import rpyc; import numpy" 2>/dev/null || {
    log ERROR "[python-linux] FATAL: Required packages missing (mt5linux, rpyc, numpy)"
    exit 1
}

log INFO "[python-linux] All packages installed and verified"
