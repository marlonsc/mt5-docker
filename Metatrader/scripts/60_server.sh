#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

log INFO "[7/7] Starting the mt5linux server..."
python3 -m mt5linux --host 0.0.0.0 -p "$mt5server_port" -w "$wine_executable" python.exe &

sleep 5

if ss -tuln | grep ":$mt5server_port" > /dev/null; then
    log INFO "[7/7] The mt5linux server is running on port $mt5server_port."
else
    log ERROR "[7/7] Failed to start the mt5linux server on port $mt5server_port."
fi