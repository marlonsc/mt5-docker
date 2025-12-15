#!/bin/bash
# Verify Linux Python packages (FAIL-FAST)
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[python-linux] Verifying Linux Python packages..."

python3 -c "from mt5linux import MetaTrader5; import rpyc; import numpy" 2>/dev/null || {
    log ERROR "[python-linux] FATAL: Required packages missing (mt5linux, rpyc, numpy)"
    exit 1
}

log INFO "[python-linux] All packages verified"
