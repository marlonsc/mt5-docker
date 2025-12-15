#!/bin/bash
# Verify Wine Python installation (FAIL-FAST)
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[python-wine] Verifying Wine Python..."

if [ ! -f "$WINE_PYTHON_PATH" ]; then
    log ERROR "[python-wine] FATAL: Wine Python not found at $WINE_PYTHON_PATH"
    exit 1
fi

PYTHON_VER=$("$wine_executable" "$WINE_PYTHON_PATH" --version 2>&1) || {
    log ERROR "[python-wine] FATAL: Wine Python cannot execute"
    exit 1
}

"$wine_executable" "$WINE_PYTHON_PATH" -c "import rpyc, numpy, pydantic" 2>/dev/null || {
    log ERROR "[python-wine] FATAL: Base packages missing"
    exit 1
}

log INFO "[python-wine] $PYTHON_VER verified"
