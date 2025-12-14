#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

EXPERTS_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/MQL5/Experts"
LIBRARIES_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/MQL5/Libraries"

log INFO "[6/9] Ensuring Myfxbook Expert and Library are present..."

mkdir -p "$EXPERTS_DIR" "$LIBRARIES_DIR"

# Check if already installed
if [ -f "$MYFXBOOK_MARKER" ] && [ -f "$EXPERTS_DIR/Myfxbook.ex5" ] && [ -f "$LIBRARIES_DIR/Myfxbook.dll" ]; then
    log INFO "[6/9] Myfxbook already installed; skipping download"
    exit 0
fi

# Download Myfxbook files with caching
log INFO "[6/9] Downloading Myfxbook files..."

# Try cache first, then download
if [ -f "$CACHE_DIR/Myfxbook.ex5" ]; then
    log INFO "Using cached: Myfxbook.ex5"
    cp "$CACHE_DIR/Myfxbook.ex5" "$EXPERTS_DIR/Myfxbook.ex5"
else
    wget -q --user-agent="Mozilla/5.0" "https://www.myfxbook.com/pages/Myfxbook.ex5" -O "$EXPERTS_DIR/Myfxbook.ex5" || true
    # Cache for next time
    cp "$EXPERTS_DIR/Myfxbook.ex5" "$CACHE_DIR/Myfxbook.ex5" 2>/dev/null || true
fi

if [ -f "$CACHE_DIR/Myfxbook.dll" ]; then
    log INFO "Using cached: Myfxbook.dll"
    cp "$CACHE_DIR/Myfxbook.dll" "$LIBRARIES_DIR/Myfxbook.dll"
else
    wget -q --user-agent="Mozilla/5.0" "https://www.myfxbook.com/pages/mt5_64/Myfxbook.dll" -O "$LIBRARIES_DIR/Myfxbook.dll" || true
    # Cache for next time
    cp "$LIBRARIES_DIR/Myfxbook.dll" "$CACHE_DIR/Myfxbook.dll" 2>/dev/null || true
fi

chmod 644 "$EXPERTS_DIR/Myfxbook.ex5" "$LIBRARIES_DIR/Myfxbook.dll" 2>/dev/null || true

# Mark as installed
touch "$MYFXBOOK_MARKER"
log INFO "[6/9] Myfxbook installation complete"
