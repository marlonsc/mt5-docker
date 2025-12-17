#!/bin/bash
# MT5 Health Monitor
# =============================================================================
# Monitors MT5 terminal and bridge health. Signals restart via token file.
# svc-mt5server is responsible for actual restart execution.
#
# Token-based communication:
# - Reads:  /tmp/.mt5-startup-complete (start.sh signals ready)
# - Writes: /tmp/.mt5-restart-requested (signals svc-mt5server to restart)
# =============================================================================
set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
CONFIG_DIR="${CONFIG_DIR:-/config}"
WINEPREFIX="${WINEPREFIX:-$CONFIG_DIR/.wine}"
mt5server_port="${mt5server_port:-8001}"

# Health check settings
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"
FAILURE_THRESHOLD="${FAILURE_THRESHOLD:-3}"  # Consecutive failures before restart

# Token files
STARTUP_MARKER="${STARTUP_MARKER:-/tmp/.mt5-startup-complete}"
RESTART_TOKEN="${RESTART_TOKEN:-/tmp/.mt5-restart-requested}"
STARTUP_WAIT_MAX=300

# State tracking
MT5_FAILURE_COUNT=0
BRIDGE_FAILURE_COUNT=0

# =============================================================================
# LOGGING
# =============================================================================
log() {
    local level="$1"; shift
    printf '[%s] [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$*"
}

# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================

check_mt5_process() {
    pgrep -f "terminal64.exe" > /dev/null 2>&1
}

check_bridge_listening() {
    # Use ss (iproute2) - available on modern Linux images
    # netstat is NOT available in Alpine/minimal containers
    ss -tuln 2>/dev/null | grep -q ":$mt5server_port"
}

check_bridge_responding() {
    # Use nc (netcat) for TCP check - more portable than /dev/tcp
    nc -z localhost "$mt5server_port" 2>/dev/null
}

# =============================================================================
# TOKEN FUNCTIONS
# =============================================================================

request_restart() {
    local reason="$1"
    log WARN "[health] Requesting restart: $reason"
    echo "$reason" > "$RESTART_TOKEN"
}

is_restart_pending() {
    [ -f "$RESTART_TOKEN" ]
}

# =============================================================================
# MAIN HEALTH MONITOR LOOP
# =============================================================================

wait_for_startup() {
    local waited=0
    while [ ! -f "$STARTUP_MARKER" ] && [ $waited -lt $STARTUP_WAIT_MAX ]; do
        log INFO "[health] Waiting for startup to complete..."
        sleep 10
        waited=$((waited + 10))
    done

    if [ ! -f "$STARTUP_MARKER" ]; then
        log ERROR "[health] Startup marker not found after ${STARTUP_WAIT_MAX}s"
        exit 1
    fi
    log INFO "[health] Startup complete, beginning health monitoring"
}

main_loop() {
    log INFO "[health] Starting health monitor (interval: ${HEALTH_CHECK_INTERVAL}s, threshold: ${FAILURE_THRESHOLD})"

    wait_for_startup

    while true; do
        sleep "$HEALTH_CHECK_INTERVAL"

        # Skip if restart already pending
        if is_restart_pending; then
            log DEBUG "[health] Restart pending, waiting..."
            continue
        fi

        # Check MT5 terminal process
        if ! check_mt5_process; then
            MT5_FAILURE_COUNT=$((MT5_FAILURE_COUNT + 1))
            log WARN "[health] MT5 not running (failure $MT5_FAILURE_COUNT/$FAILURE_THRESHOLD)"
            if [ "$MT5_FAILURE_COUNT" -ge "$FAILURE_THRESHOLD" ]; then
                request_restart "MT5 terminal not running"
                MT5_FAILURE_COUNT=0
            fi
            continue
        fi
        MT5_FAILURE_COUNT=0

        # Check bridge listening
        if ! check_bridge_listening; then
            BRIDGE_FAILURE_COUNT=$((BRIDGE_FAILURE_COUNT + 1))
            log WARN "[health] Bridge not listening (failure $BRIDGE_FAILURE_COUNT/$FAILURE_THRESHOLD)"
            if [ "$BRIDGE_FAILURE_COUNT" -ge "$FAILURE_THRESHOLD" ]; then
                request_restart "Bridge not listening on port $mt5server_port"
                BRIDGE_FAILURE_COUNT=0
            fi
            continue
        fi

        # Check bridge responding
        if ! check_bridge_responding; then
            BRIDGE_FAILURE_COUNT=$((BRIDGE_FAILURE_COUNT + 1))
            log WARN "[health] Bridge not responding (failure $BRIDGE_FAILURE_COUNT/$FAILURE_THRESHOLD)"
            if [ "$BRIDGE_FAILURE_COUNT" -ge "$FAILURE_THRESHOLD" ]; then
                request_restart "Bridge not responding to connections"
                BRIDGE_FAILURE_COUNT=0
            fi
            continue
        fi
        BRIDGE_FAILURE_COUNT=0

        log DEBUG "[health] All checks passed"
    done
}

# =============================================================================
# ENTRY POINT
# =============================================================================

if [ "${1:-}" = "--daemon" ]; then
    main_loop &
    log INFO "[health] Health monitor started in background (PID: $!)"
else
    main_loop
fi
