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
# DLL overrides:
# - mscoree=n,mshtml=n: Disable Mono/Gecko prompts
# - ucrtbase=n: Use native ucrtbase.dll for numpy 2.x compatibility (crealf fix)
export WINEDLLOVERRIDES="mscoree=n,mshtml=n,ucrtbase=n"
export DISPLAY="${DISPLAY:-:0}"

# Suppress all Wine debug output for cleaner logs
export WINEDEBUG="${WINEDEBUG:--all}"

# Ensure winetricks cache directory exists with proper permissions
mkdir -p /config/.cache/winetricks
chmod 755 /config/.cache/winetricks
export XDG_CACHE_HOME="/config/.cache"

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

# Native ucrtbase.dll for numpy 2.x compatibility (crealf function)
# Wine 10.0's builtin ucrtbase.dll doesn't implement crealf()
run_winetricks ucrtbase || true

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
