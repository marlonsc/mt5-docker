#!/bin/bash
# MT5 Health Monitor and Auto-Recovery
# Runs in background to ensure MT5 stays running and connected
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# Configuration
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"
AUTO_RECOVERY_ENABLED="${AUTO_RECOVERY_ENABLED:-1}"
MAX_RESTART_ATTEMPTS=3
RESTART_COOLDOWN=60

# State tracking
RESTART_COUNT=0
LAST_RESTART_TIME=0

# ============================================================
# Health Check Functions
# ============================================================

check_mt5_process() {
    pgrep -f "terminal64.exe" > /dev/null 2>&1
    return $?
}

check_rpyc_server() {
    ss -tuln | grep -q ":$mt5server_port" 2>/dev/null
    return $?
}

check_mt5_connection() {
    # Quick TCP check to RPyC server
    timeout 5 bash -c "echo >/dev/tcp/localhost/$mt5server_port" 2>/dev/null
    return $?
}

# ============================================================
# Recovery Functions
# ============================================================

restart_mt5() {
    local current_time
    current_time=$(date +%s)
    local time_since_last=$((current_time - LAST_RESTART_TIME))

    # Check cooldown
    if [ "$time_since_last" -lt "$RESTART_COOLDOWN" ]; then
        log WARN "[health] Restart cooldown active (${time_since_last}s < ${RESTART_COOLDOWN}s)"
        return 1
    fi

    # Check restart limit
    if [ "$RESTART_COUNT" -ge "$MAX_RESTART_ATTEMPTS" ]; then
        log ERROR "[health] Max restart attempts reached ($MAX_RESTART_ATTEMPTS). Manual intervention required."
        return 1
    fi

    log INFO "[health] Attempting MT5 restart (attempt $((RESTART_COUNT + 1))/$MAX_RESTART_ATTEMPTS)..."

    # Kill existing MT5 process if hanging
    pkill -9 -f "terminal64.exe" 2>/dev/null || true
    sleep 2

    # Build MT5 launch arguments with portable mode and config file
    MT5_ARGS="/portable"
    MT5_CONFIG_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/Config"
    MT5_STARTUP_INI="$MT5_CONFIG_DIR/startup.ini"

    if [ -f "$MT5_STARTUP_INI" ]; then
        MT5_ARGS="$MT5_ARGS /config:\"C:\\Program Files\\MetaTrader 5\\Config\\startup.ini\""
        log INFO "[health] Restarting with config file"
    elif [ -n "${MT5_LOGIN:-}" ] && [ -n "${MT5_PASSWORD:-}" ] && [ -n "${MT5_SERVER:-}" ]; then
        MT5_ARGS="$MT5_ARGS /login:${MT5_LOGIN} /password:${MT5_PASSWORD} /server:${MT5_SERVER}"
        log INFO "[health] Restarting with auto-login for account ${MT5_LOGIN}"
    fi

    # Restart MT5
    "$wine_executable" "$mt5file" $MT5_ARGS &

    RESTART_COUNT=$((RESTART_COUNT + 1))
    LAST_RESTART_TIME=$current_time

    # Wait for startup
    sleep 15

    if check_mt5_process; then
        log INFO "[health] MT5 restarted successfully"
        # Reset counter after successful restart
        RESTART_COUNT=0
        return 0
    else
        log ERROR "[health] MT5 restart failed"
        return 1
    fi
}

restart_rpyc_server() {
    log INFO "[health] Restarting RPyC server..."

    # Kill the Wine Python process - s6 will automatically restart it
    # Note: s6-svc requires root, but this script runs as abc user
    pkill -f "python.exe /tmp/mt5linux/server.py" 2>/dev/null || true

    # Wait for s6 to restart the service
    sleep 5

    if check_rpyc_server; then
        log INFO "[health] RPyC server restarted successfully on port $mt5server_port"
        return 0
    else
        log ERROR "[health] RPyC server restart failed"
        return 1
    fi
}

# ============================================================
# Main Health Monitor Loop
# ============================================================

main_loop() {
    log INFO "[health] Starting health monitor (interval: ${HEALTH_CHECK_INTERVAL}s, auto-recovery: ${AUTO_RECOVERY_ENABLED})"

    while true; do
        sleep "$HEALTH_CHECK_INTERVAL"

        # Check MT5 process
        if ! check_mt5_process; then
            log WARN "[health] MT5 terminal not running!"
            if [ "$AUTO_RECOVERY_ENABLED" = "1" ]; then
                restart_mt5
            fi
            continue
        fi

        # Check RPyC server
        if ! check_rpyc_server; then
            log WARN "[health] RPyC server not listening on port $mt5server_port!"
            if [ "$AUTO_RECOVERY_ENABLED" = "1" ]; then
                restart_rpyc_server
            fi
            continue
        fi

        # Check connection health
        if ! check_mt5_connection; then
            log WARN "[health] RPyC server not responding to connections!"
            if [ "$AUTO_RECOVERY_ENABLED" = "1" ]; then
                restart_rpyc_server
            fi
            continue
        fi

        # All checks passed - reset restart counter if it's been a while
        local current_time
        current_time=$(date +%s)
        if [ "$RESTART_COUNT" -gt 0 ] && [ $((current_time - LAST_RESTART_TIME)) -gt 300 ]; then
            log INFO "[health] System stable for 5 minutes, resetting restart counter"
            RESTART_COUNT=0
        fi
    done
}

# ============================================================
# Entry Point
# ============================================================

if [ "${1:-}" = "--daemon" ]; then
    # Run in daemon mode
    main_loop &
    log INFO "[health] Health monitor started in background (PID: $!)"
else
    # Run in foreground
    main_loop
fi
