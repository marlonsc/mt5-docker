#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

if [ ! -f "$DEPS_MARKER" ]; then
    log INFO "[1/7] Installing Winetricks components (dotnet48, corefonts, vcrun2019, win10, fontsmooth, gdiplus, msxml6, msls31, riched20, iertutil, wininet, d3dcompiler_47)"
    export WINETRICKS_UNATTENDED=1
    env WINEPREFIX="$WINEPREFIX" winetricks -q -f dotnet48 || true
    env WINEPREFIX="$WINEPREFIX" winetricks -q -f corefonts win10 fontsmooth=rgb || true
    env WINEPREFIX="$WINEPREFIX" winetricks -q -f vcrun2019 gdiplus msxml6 msls31 riched20 iertutil wininet d3dcompiler_47 vcrun2015 vcrun2017 vcrun2022 ucrtbase || true
    touch "$DEPS_MARKER"
else
    log INFO "[1/7] Skipping Winetricks components; marker present at $DEPS_MARKER"
fi

log INFO "[2/7] Listing installed Winetricks components"
env WINEPREFIX="$WINEPREFIX" winetricks list-installed || true