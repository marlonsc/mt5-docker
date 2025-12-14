#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[1/9] Initializing Wine prefix (WINEPREFIX=$WINEPREFIX)"

mkdir -p "$PREFIX_CACHE_DIR" || true

# Check if Wine prefix is already fully initialized
if [ -f "$INIT_MARKER" ] && [ -f "$DEPS_MARKER" ]; then
    log INFO "[1/9] Wine prefix already initialized; skipping wineboot"
else
    "$wine_executable" wineboot -i || log WARN "wineboot returned non-zero"
fi

# Gecko MSI filenames (based on version)
GECKO_X64_FILE="wine-gecko-${GECKO_VERSION}-x86_64.msi"
GECKO_X86_FILE="wine-gecko-${GECKO_VERSION}-x86.msi"
GECKO_X64="$PREFIX_CACHE_DIR/$GECKO_X64_FILE"
GECKO_X86="$PREFIX_CACHE_DIR/$GECKO_X86_FILE"

# Get Gecko files using prioritized cache
if [ ! -f "$GECKO_X64" ]; then
    get_file "$GECKO_X64_FILE" \
        "https://dl.winehq.org/wine/wine-gecko/${GECKO_VERSION}/$GECKO_X64_FILE" \
        "$GECKO_X64"
fi

if [ ! -f "$GECKO_X86" ]; then
    get_file "$GECKO_X86_FILE" \
        "https://dl.winehq.org/wine/wine-gecko/${GECKO_VERSION}/$GECKO_X86_FILE" \
        "$GECKO_X86"
fi

# Install Gecko if not already done
if [ ! -f "$GECKO_MARKER" ]; then
    if [ -f "$GECKO_X64" ]; then
        log INFO "[1/9] Installing Wine Gecko x64 into prefix"
        "$wine_executable" msiexec /i "$GECKO_X64" /quiet || log WARN "Gecko x64 MSI install returned non-zero"
    fi
    if [ -f "$GECKO_X86" ]; then
        log INFO "[1/9] Installing Wine Gecko x86 into prefix"
        "$wine_executable" msiexec /i "$GECKO_X86" /quiet || log WARN "Gecko x86 MSI install returned non-zero"
    fi
    touch "$GECKO_MARKER"
else
    log INFO "[1/9] Skipping Wine Gecko install; marker present"
fi

# Update the Wine prefix after installs (only if not already done)
if [ ! -f "$INIT_MARKER" ]; then
    "$wine_executable" wineboot -u || log WARN "wineboot -u returned non-zero"
    touch "$INIT_MARKER"
else
    log INFO "[1/9] Skipping wineboot -u; prefix already updated"
fi
