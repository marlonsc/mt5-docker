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

# Helper function
run_winetricks() {
    local component="$1"
    log INFO "[winetricks] Installing: ${component}..."
    winetricks -q "$component" 2>/dev/null || {
        log WARN "[winetricks] ${component} failed (non-critical)"
        return 0
    }
}

# Install components required for MT5 installer
# vcrun2019/2022: Visual C++ runtime (required by MT5)
# corefonts: Windows fonts (required for UI)
log INFO "[winetricks] Installing Visual C++ runtime and fonts..."
run_winetricks vcrun2019
run_winetricks vcrun2022
run_winetricks corefonts

# Mark as done
touch "$DEPS_MARKER"
log INFO "[winetricks] Wine components installed"
