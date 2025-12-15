#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# Server configuration from environment
mt5server_port=${mt5server_port:-8001}

log INFO "[server] Configuration complete"
log INFO "[server] RPyC server managed by s6-overlay supervisor"
log INFO "[server] Service: svc-mt5server, Port: ${mt5server_port}"

# The actual RPyC server is started and supervised by s6-overlay service
# See: /etc/s6-overlay/s6-rc.d/svc-mt5server/run
#
# s6-overlay provides:
# - Automatic restart on crash
# - Clean shutdown on container stop
# - Integrated logging
#
# To manually restart the server:
#   s6-svc -r /run/service/svc-mt5server
#
# To check service status:
#   s6-svstat /run/service/svc-mt5server
