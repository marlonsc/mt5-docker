#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# Paths inside the Wine prefix
EXPERTS_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/MQL5/Experts"
DOCS_DIR="$WINEPREFIX/drive_c/users/$(whoami)/Documents"

if [ -d "/data" ]; then
    mkdir -p "$EXPERTS_DIR" "$DOCS_DIR"

    # Copy Expert Advisors
    if [ -d "/data/ea" ]; then
        log INFO "Syncing /data/ea -> $EXPERTS_DIR"
        rsync -a --delete "/data/ea/" "$EXPERTS_DIR/"
    else
        log INFO "No /data/ea directory found; skipping Experts sync"
    fi

    # Copy set-files into Documents
    if [ -d "/data/set-files" ]; then
        log INFO "Syncing /data/set-files -> $DOCS_DIR"
        rsync -a --delete "/data/set-files/" "$DOCS_DIR/"
    else
        log INFO "No /data/set-files directory found; skipping Documents sync"
    fi

    log INFO "Data sync completed"
fi
