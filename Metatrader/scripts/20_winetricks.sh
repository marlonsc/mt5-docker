#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# ============================================================
# Wine dependencies installation/upgrade
# Always runs to ensure components are up to date
# All operations are SILENT - no prompts, no user interaction
# ============================================================

# Force unattended mode - NEVER prompt for anything
export WINETRICKS_UNATTENDED=1
# DLL overrides: Disable Mono/Gecko prompts
# Note: ucrtbase override removed - Wine 10.1+ has native crealf() support for numpy 2.x
export WINEDLLOVERRIDES="mscoree=n,mshtml=n"
export DISPLAY="${DISPLAY:-:0}"

# Suppress all Wine debug output for cleaner logs
export WINEDEBUG="${WINEDEBUG:--all}"

# Winetricks cache directory - use /config/.cache or fallback to $HOME/.cache
# (10_prefix_init.sh sets XDG_CACHE_HOME, but we handle both cases)
if [ -d "/config/.cache/winetricks" ] && [ -w "/config/.cache/winetricks" ]; then
    export XDG_CACHE_HOME="/config/.cache"
else
    # Fallback to home directory cache
    mkdir -p "$HOME/.cache/winetricks" 2>/dev/null || true
    export XDG_CACHE_HOME="$HOME/.cache"
    log WARN "[winetricks] Using fallback cache: $HOME/.cache/winetricks"
fi

log INFO "[winetricks] Upgrading Wine dependencies (silent mode)..."

# Helper function for silent winetricks
run_winetricks() {
    local component="$1"
    log INFO "[winetricks] Installing/upgrading: ${component}"
    if ! env WINEPREFIX="$WINEPREFIX" WINETRICKS_UNATTENDED=1 winetricks -q -f "$component" </dev/null >/dev/null 2>&1; then
        log WARN "[winetricks] ${component} failed (non-critical)"
        return 1
    fi
    return 0
}

# Windows 10 compatibility mode (required first)
run_winetricks win10 || true

# Visual C++ runtimes (recommended for EAs)
run_winetricks vcrun2019 || true
run_winetricks vcrun2022 || true

# Graphics and fonts
run_winetricks corefonts || true
run_winetricks gdiplus || true

# XML support
run_winetricks msxml6 || true

# .NET Framework (optional, controlled by ENABLE_WIN_DOTNET)
if [ "${ENABLE_WIN_DOTNET:-1}" = "1" ]; then
    log INFO "[winetricks] Installing dotnet48 (for .NET EAs) - this may take a while..."
    run_winetricks dotnet48 || log WARN "[winetricks] dotnet48 failed - .NET EAs will not work"
else
    log INFO "[winetricks] Skipping dotnet48 (ENABLE_WIN_DOTNET=0)"
fi

# Mark as done (for logging purposes only, upgrades still run)
touch "$DEPS_MARKER"
log INFO "[winetricks] Dependency upgrade complete"
