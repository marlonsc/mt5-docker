#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# Check if data sync is enabled
if [ "${ENABLE_DATA_SYNC:-1}" != "1" ]; then
    log INFO "[5/9] Data sync disabled (ENABLE_DATA_SYNC=${ENABLE_DATA_SYNC:-0})"
    exit 0
fi

# Paths inside the Wine prefix
EXPERTS_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/MQL5/Experts"
DOCS_DIR="$WINEPREFIX/drive_c/users/$(whoami)/Documents"

if [ -d "/data" ]; then
    mkdir -p "$EXPERTS_DIR" "$DOCS_DIR"

    # Copy Expert Advisors
    if [ -d "/data/ea" ]; then
        log INFO "[5/9] Syncing /data/ea -> $EXPERTS_DIR"
        rsync -a --delete "/data/ea/" "$EXPERTS_DIR/"
    else
        log INFO "[5/9] No /data/ea directory found; skipping Experts sync"
    fi

    # Copy set-files into Documents
    if [ -d "/data/set-files" ]; then
        log INFO "[5/9] Syncing /data/set-files -> $DOCS_DIR"
        rsync -a --delete "/data/set-files/" "$DOCS_DIR/"
    else
        log INFO "[5/9] No /data/set-files directory found; skipping Documents sync"
    fi

    log INFO "[5/9] Data sync completed"
fi
