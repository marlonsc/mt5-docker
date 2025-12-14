#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# Resilient server configuration from environment
RPYC_RESILIENT="${RPYC_RESILIENT:-1}"
RPYC_HEALTH_PORT="${RPYC_HEALTH_PORT:-8002}"
RPYC_MAX_RESTARTS="${RPYC_MAX_RESTARTS:-10}"
RPYC_MAX_CONNECTIONS="${RPYC_MAX_CONNECTIONS:-10}"

log INFO "[9/9] Starting the mt5linux server..."

if [ "$RPYC_RESILIENT" = "1" ]; then
    log INFO "[9/9] Using resilient server with supervisor and health checks"
    python3 -m mt5linux.resilient_server \
        --host 0.0.0.0 \
        -p "$mt5server_port" \
        -w "$wine_executable" \
        --health-port "$RPYC_HEALTH_PORT" \
        --max-restarts "$RPYC_MAX_RESTARTS" \
        --max-connections "$RPYC_MAX_CONNECTIONS" \
        python.exe &
else
    log INFO "[9/9] Using basic server via Wine (mt5linux code generator)"
    # mt5linux Wine mode: generates server script and runs it via Wine with Windows Python
    # This is required because MetaTrader5 API only works inside Wine
    python3 -m mt5linux \
        --host 0.0.0.0 \
        -p "$mt5server_port" \
        -w "$wine_executable" \
        python.exe &
fi

# Wait for server to start
sleep 5

# Check if main RPyC port is listening
if ss -tuln | grep -q ":$mt5server_port"; then
    log INFO "[9/9] RPyC server is running on port $mt5server_port"
else
    log ERROR "[9/9] Failed to start RPyC server on port $mt5server_port"
fi

# Check health endpoint if resilient mode
if [ "$RPYC_RESILIENT" = "1" ]; then
    if ss -tuln | grep -q ":$RPYC_HEALTH_PORT"; then
        log INFO "[9/9] Health endpoint available on port $RPYC_HEALTH_PORT"
    else
        log WARN "[9/9] Health endpoint not available on port $RPYC_HEALTH_PORT"
    fi
fi