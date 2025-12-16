#!/bin/bash
# Copy bridge.py to Wine Python for RPyC server
# bridge.py is bundled with the container (no external download needed)
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[copy-bridge] Copying bridge.py to Wine Python..."

# Source bridge.py location (bundled with container)
BRIDGE_SOURCE="/Metatrader/bridge.py"

if [ ! -f "$BRIDGE_SOURCE" ]; then
    log ERROR "[copy-bridge] FATAL: bridge.py not found at $BRIDGE_SOURCE"
    exit 1
fi

# Wine Python site-packages location
WINE_SITE_PACKAGES="$WINEPREFIX/drive_c/Python/Lib/site-packages"

if [ ! -d "$WINE_SITE_PACKAGES" ]; then
    log ERROR "[copy-bridge] Wine Python site-packages not found: $WINE_SITE_PACKAGES"
    exit 1
fi

# Create mt5linux package directory
mkdir -p "$WINE_SITE_PACKAGES/mt5linux" 2>&1 || {
    log ERROR "[copy-bridge] Failed to create mt5linux directory"
    exit 1
}

# Copy bridge.py (standalone, uses only logging + rpyc)
cp "$BRIDGE_SOURCE" "$WINE_SITE_PACKAGES/mt5linux/" 2>&1 || {
    log ERROR "[copy-bridge] Failed to copy bridge.py to Wine Python"
    exit 1
}

# Create minimal __init__.py for module import
cat > "$WINE_SITE_PACKAGES/mt5linux/__init__.py" << 'EOF'
"""Minimal mt5linux for Wine - only bridge module."""
EOF

# Verify copy
if [ -f "$WINE_SITE_PACKAGES/mt5linux/bridge.py" ]; then
    log INFO "[copy-bridge] bridge.py installed: $WINE_SITE_PACKAGES/mt5linux/bridge.py"
else
    log ERROR "[copy-bridge] bridge.py copy verification failed"
    exit 1
fi

log INFO "[copy-bridge] RPyC bridge setup complete"
