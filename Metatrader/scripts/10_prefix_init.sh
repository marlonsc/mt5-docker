#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[wine] Initializing Wine prefix (WINEPREFIX=$WINEPREFIX)"

# Create all required cache directories upfront
log INFO "[wine] Creating cache directories..."

# Wine prefix cache (for Gecko MSIs, etc)
if ! mkdir -p "$PREFIX_CACHE_DIR" 2>/dev/null; then
    log WARN "[wine] Failed to create Wine cache dir: $PREFIX_CACHE_DIR"
    # Non-fatal - Gecko can be downloaded directly
fi

# Winetricks cache (for vcrun, dotnet, etc)
# Try /config/.cache first, fall back to $HOME/.cache if permission denied
WINETRICKS_CACHE_DIR="/config/.cache/winetricks"
if mkdir -p "$WINETRICKS_CACHE_DIR" 2>/dev/null && [ -w "$WINETRICKS_CACHE_DIR" ]; then
    export XDG_CACHE_HOME="/config/.cache"
    log INFO "[wine] Using winetricks cache: $WINETRICKS_CACHE_DIR"
else
    log WARN "[wine] /config/.cache not writable, using fallback"
    WINETRICKS_CACHE_DIR="$HOME/.cache/winetricks"
    mkdir -p "$WINETRICKS_CACHE_DIR" 2>/dev/null || true
    export XDG_CACHE_HOME="$HOME/.cache"
    log INFO "[wine] Using winetricks cache: $WINETRICKS_CACHE_DIR"
fi

# Check if Wine prefix is already fully initialized
if [ -f "$INIT_MARKER" ] && [ -f "$DEPS_MARKER" ]; then
    log INFO "[wine] Prefix already initialized; skipping wineboot"
else
    if ! "$wine_executable" wineboot -i; then
        log ERROR "[wine] wineboot -i failed"
        exit 1
    fi
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
        log INFO "[wine] Installing Gecko x64 into prefix"
        if ! "$wine_executable" msiexec /i "$GECKO_X64" /quiet; then
            log ERROR "[wine] Gecko x64 install failed"
            exit 1
        fi
    fi
    if [ -f "$GECKO_X86" ]; then
        log INFO "[wine] Installing Gecko x86 into prefix"
        if ! "$wine_executable" msiexec /i "$GECKO_X86" /quiet; then
            log ERROR "[wine] Gecko x86 install failed"
            exit 1
        fi
    fi
    touch "$GECKO_MARKER"
else
    log INFO "[wine] Gecko already installed; skipping"
fi

# Update the Wine prefix after installs (only if not already done)
if [ ! -f "$INIT_MARKER" ]; then
    if ! "$wine_executable" wineboot -u; then
        log ERROR "[wine] wineboot -u failed"
        exit 1
    fi
    touch "$INIT_MARKER"
else
    log INFO "[wine] Prefix already updated; skipping wineboot -u"
fi
