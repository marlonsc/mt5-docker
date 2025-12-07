#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

if [ -d "/data" ]; then
    log INFO "Syncing /data into Wine Documents at $DOCS_DIR"
    mkdir -p "$DOCS_DIR"
    cp -a "/data/." "$DOCS_DIR/" 2>/dev/null || log ERROR "cp failed copying /data to Documents"
    log INFO "Data copy block completed"
fi