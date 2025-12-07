#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "Ensuring Myfxbook Expert and Library are present..."
EXPERTS_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/MQL5/Experts"
LIBRARIES_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/MQL5/Libraries"

mkdir -p "$EXPERTS_DIR" "$LIBRARIES_DIR"
wget -q --user-agent="Mozilla/5.0" "https://www.myfxbook.com/pages/Myfxbook.ex5" -O "$EXPERTS_DIR/Myfxbook.ex5" || true
wget -q --user-agent="Mozilla/5.0" "https://www.myfxbook.com/pages/mt5_64/Myfxbook.dll" -O "$LIBRARIES_DIR/Myfxbook.dll" || true

chmod 644 "$EXPERTS_DIR/Myfxbook.ex5" "$LIBRARIES_DIR/Myfxbook.dll" 2>/dev/null || true