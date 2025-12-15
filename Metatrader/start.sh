#!/bin/bash
set -euo pipefail

# Orchestrator: source shared env and run all scripts in order
START_TS=$(date +%s)
SCRIPTS_DIR="$(dirname "$0")/scripts"
STARTUP_MARKER="$WINEPREFIX/.startup-complete"

source "$SCRIPTS_DIR/00_env.sh"

# Remove stale startup marker (from previous runs)
rm -f "$STARTUP_MARKER"

# Count executable scripts (excluding 00_env.sh)
SCRIPT_COUNT=$(find "$SCRIPTS_DIR" -maxdepth 1 -name '[0-9]*.sh' ! -name '00_env.sh' -executable | wc -l)
log INFO "[startup] Starting MT5 setup ($SCRIPT_COUNT scripts)"

# Run all numbered scripts in order (excluding 00_env.sh which is sourced)
CURRENT=0
for script in "$SCRIPTS_DIR"/[0-9]*.sh; do
    # Skip env script (it's sourced, not executed)
    if [[ "$(basename "$script")" == "00_env.sh" ]]; then
        continue
    fi

    CURRENT=$((CURRENT + 1))
    SCRIPT_NAME=$(basename "$script")
    log INFO "[$CURRENT/$SCRIPT_COUNT] Running $SCRIPT_NAME"

    if ! "$script"; then
        log ERROR "[$CURRENT/$SCRIPT_COUNT] $SCRIPT_NAME failed - aborting startup"
        exit 1
    fi
done

END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))

# If we reach here, all scripts passed (fail-fast exits on first failure)
log INFO "[startup] MT5 setup completed in ${ELAPSED}s (all scripts passed)"
touch "$STARTUP_MARKER"
export STARTUP_MARKER

# Note: MT5 login is handled by 30_mt5.sh via generate_config + launch_mt5
# No additional login step needed here

# Start health monitor in background if auto-recovery is enabled and startup succeeded
if [ "${AUTO_RECOVERY_ENABLED:-1}" = "1" ] && [ -f "$STARTUP_MARKER" ]; then
    "$(dirname "$0")/health_monitor.sh" --daemon
fi
