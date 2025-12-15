#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# ============================================================
# Wine dependencies installation
# ============================================================
# All winetricks dependencies are OPTIONAL - MT5 can run without them.
# We log warnings on failure but don't exit, since:
# - winetricks can fail for transient network/version issues
# - MT5 terminal can function without most of these
# - User can retry or diagnose from logs
# ============================================================

if [ ! -f "$DEPS_MARKER" ]; then
    export WINETRICKS_UNATTENDED=1

    # Visual C++ runtime (recommended for EAs)
    log INFO "[winetricks] Installing vcrun2019 (recommended)"
    if ! env WINEPREFIX="$WINEPREFIX" winetricks -q -f vcrun2019; then
        log WARN "[winetricks] vcrun2019 failed - some EAs may not work"
    fi

    # Graphics and fonts
    log INFO "[winetricks] Installing corefonts, gdiplus, msxml6"
    env WINEPREFIX="$WINEPREFIX" winetricks -q -f corefonts || log WARN "[winetricks] corefonts failed"
    env WINEPREFIX="$WINEPREFIX" winetricks -q -f gdiplus || log WARN "[winetricks] gdiplus failed"
    env WINEPREFIX="$WINEPREFIX" winetricks -q -f msxml6 || log WARN "[winetricks] msxml6 failed"

    # Windows 10 compatibility mode
    log INFO "[winetricks] Setting win10 mode"
    env WINEPREFIX="$WINEPREFIX" winetricks -q -f win10 || log WARN "[winetricks] win10 mode failed"

    # .NET Framework (optional, controlled by ENABLE_WIN_DOTNET)
    if [ "${ENABLE_WIN_DOTNET:-1}" = "1" ]; then
        log INFO "[winetricks] Installing dotnet48 (for .NET EAs)"
        if ! env WINEPREFIX="$WINEPREFIX" winetricks -q -f dotnet48; then
            log WARN "[winetricks] dotnet48 failed - .NET EAs will not work"
        fi
    else
        log INFO "[winetricks] Skipping dotnet48 (ENABLE_WIN_DOTNET=0)"
    fi

    # Diagnostic: show what was installed
    log INFO "[winetricks] Installed components:"
    env WINEPREFIX="$WINEPREFIX" winetricks list-installed 2>/dev/null || log DEBUG "[winetricks] list-installed unavailable"

    touch "$DEPS_MARKER"
    log INFO "[winetricks] Installation complete"
else
    log INFO "[winetricks] Dependencies already installed; skipping"
fi