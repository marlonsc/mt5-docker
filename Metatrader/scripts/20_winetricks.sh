#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

if [ ! -f "$DEPS_MARKER" ]; then
    export WINETRICKS_UNATTENDED=1

    # .NET Framework (optional, controlled by ENABLE_WIN_DOTNET)
    if [ "${ENABLE_WIN_DOTNET:-1}" = "1" ]; then
        log INFO "[2/9] Installing Winetricks components (dotnet48, corefonts, vcrun2019, win10, gdiplus, msxml6)"
        env WINEPREFIX="$WINEPREFIX" winetricks -q -f dotnet48 || true
    else
        log INFO "[2/9] Installing Winetricks components (corefonts, vcrun2019, win10, gdiplus, msxml6) - dotnet48 disabled"
    fi

    env WINEPREFIX="$WINEPREFIX" winetricks -q -f corefonts || true
    env WINEPREFIX="$WINEPREFIX" winetricks -q -f vcrun2019 gdiplus msxml6 || true
    env WINEPREFIX="$WINEPREFIX" winetricks -q -f win10 || true

    # List installed components only on first run
    log INFO "[2/9] Listing installed Winetricks components"
    env WINEPREFIX="$WINEPREFIX" winetricks list-installed || true

    touch "$DEPS_MARKER"
else
    log INFO "[2/9] Skipping Winetricks components; marker present at $DEPS_MARKER"
fi