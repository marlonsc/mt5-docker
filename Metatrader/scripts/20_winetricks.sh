#!/bin/bash
# Verify Wine components (FAIL-FAST)
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[winetricks] Verifying Wine components..."

# Components MUST be installed during Docker build
if [ ! -f "$WINE_PREFIX_TEMPLATE/.build-complete" ]; then
    log ERROR "[winetricks] FATAL: Wine prefix template not built correctly"
    exit 1
fi

# Verify win10 is configured
if ! "$wine_executable" reg query 'HKLM\Software\Microsoft\Windows NT\CurrentVersion' /v ProductName 2>/dev/null | grep -q "Windows 10"; then
    log WARN "[winetricks] Windows version may not be set to win10"
fi

touch "$DEPS_MARKER"
log INFO "[winetricks] Wine components verified"
