#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

printf '[%s] [INFO] [1/7] Initializing Wine prefix (WINEPREFIX=%s)\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$WINEPREFIX" 1>&2

mkdir -p "$PREFIX_CACHE_DIR" || true

if [ ! -f "$MONO_MSI" ]; then
    log INFO "Fetching Wine Mono MSI into prefix cache"
    wget -q -o /dev/null -O "$MONO_MSI" "https://dl.winehq.org/wine/wine-mono/10.3.0/wine-mono-10.3.0-x86.msi" || log WARN "Failed to download Mono MSI"
fi
if [ ! -f "$GECKO_X64" ]; then
    log INFO "Fetching Wine Gecko x64 MSI into prefix cache"
    wget -q -o /dev/null -O "$GECKO_X64" "https://dl.winehq.org/wine/wine-gecko/2.47.4/wine-gecko-2.47.4-x86_64.msi" || log WARN "Failed to download Gecko x64 MSI"
fi
if [ ! -f "$GECKO_X86" ]; then
    log INFO "Fetching Wine Gecko x86 MSI into prefix cache"
    wget -q -o /dev/null -O "$GECKO_X86" "https://dl.winehq.org/wine/wine-gecko/2.47.4/wine-gecko-2.47.4-x86.msi" || log WARN "Failed to download Gecko x86 MSI"
fi

ORIG_WINEDLLOVERRIDES="$WINEDLLOVERRIDES"
WINEDLLOVERRIDES_TEMP="mscoree,mscoreei="
env WINEDLLOVERRIDES="$WINEDLLOVERRIDES_TEMP" "$wine_executable" wineboot -i || log WARN "wineboot returned non-zero"

if [ ! -f "$MONO_MARKER" ] && [ -f "$MONO_MSI" ]; then
    log INFO "Installing Wine Mono into prefix"
    "$wine_executable" msiexec /i "$MONO_MSI" /quiet && touch "$MONO_MARKER" || log WARN "Mono MSI install returned non-zero"
else
    log INFO "Skipping Wine Mono install; marker present"
fi

if [ ! -f "$GECKO_MARKER" ]; then
    if [ -f "$GECKO_X64" ]; then
        log INFO "Installing Wine Gecko x64 into prefix"
        "$wine_executable" msiexec /i "$GECKO_X64" /quiet || log WARN "Gecko x64 MSI install returned non-zero"
    fi
    if [ -f "$GECKO_X86" ]; then
        log INFO "Installing Wine Gecko x86 into prefix"
        "$wine_executable" msiexec /i "$GECKO_X86" /quiet || log WARN "Gecko x86 MSI install returned non-zero"
    fi
    touch "$GECKO_MARKER"
else
    log INFO "Skipping Wine Gecko install; marker present"
fi

if [ -n "$ORIG_WINEDLLOVERRIDES" ]; then
    export WINEDLLOVERRIDES="$ORIG_WINEDLLOVERRIDES"
else
    unset WINEDLLOVERRIDES
fi
"$wine_executable" wineboot -u || log WARN "wineboot -u returned non-zero"