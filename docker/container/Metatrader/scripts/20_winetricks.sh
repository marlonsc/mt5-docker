#!/bin/bash
# Install Wine components required for MT5 (runtime)
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[winetricks] Installing Wine components for MT5..."

# Check if already installed
if [ -f "$DEPS_MARKER" ]; then
    log INFO "[winetricks] Components already installed"
    exit 0
fi

# Template must exist
if [ ! -f "$WINE_PREFIX_TEMPLATE/.build-complete" ]; then
    log ERROR "[winetricks] FATAL: Wine prefix template not built correctly"
    exit 1
fi

# Set up winetricks environment
export WINETRICKS_UNATTENDED=1
export WINEDLLOVERRIDES="mscoree=n,mshtml=n"
export DISPLAY="${DISPLAY:-:0}"
export WINEDEBUG="${WINEDEBUG:--all}"

# Install Visual C++ runtime (required by MT5)
log INFO "[winetricks] Installing Visual C++ runtime..."
winetricks -q vcrun2019 2>/dev/null || log WARN "[winetricks] vcrun2019 failed (non-critical)"

# Fonts: Liberation fonts installed in Docker base image (fonts-liberation package)
# No need to download fonts via winetricks

# IMPORTANT: Restore Windows 10 version after vcrun installation
# vcrun2019 changes Windows version to win7 which breaks MT5
log INFO "[winetricks] Restoring Windows 10 version..."
winetricks -q win10 2>/dev/null || log WARN "[winetricks] win10 restore failed"

# Mark as done
touch "$DEPS_MARKER"
log INFO "[winetricks] Wine components installed"
