#!/bin/bash
# Initialize Wine prefix from template (FAIL-FAST)
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[wine] Initializing Wine prefix..."

# Template MUST exist
if [ ! -f "$WINE_PREFIX_TEMPLATE/.build-complete" ]; then
    log ERROR "[wine] FATAL: Wine prefix template not found"
    exit 1
fi

# Copy template to /config/.wine if not initialized
if [ ! -f "$WINEPREFIX/.build-complete" ]; then
    log INFO "[wine] Copying template to $WINEPREFIX..."
    mkdir -p "$WINEPREFIX"
    cp -a "$WINE_PREFIX_TEMPLATE/." "$WINEPREFIX/"
    log INFO "[wine] Wine prefix initialized"
else
    log INFO "[wine] Wine prefix already initialized"
fi

# Wine Python MUST exist
if [ ! -f "$WINE_PYTHON_PATH" ]; then
    log ERROR "[wine] FATAL: Wine Python not found at $WINE_PYTHON_PATH"
    exit 1
fi

touch "$INIT_MARKER"
log INFO "[wine] Ready"
