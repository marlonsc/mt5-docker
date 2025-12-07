#!/bin/bash
set -euo pipefail

# Orchestrator: source shared env and run modular steps
START_TS=$(date +%s)
SCRIPTS_DIR="$(dirname "$0")/scripts"
source "$SCRIPTS_DIR/00_env.sh"

log INFO "[0/7] Starting modular MT5 setup"

"$SCRIPTS_DIR/10_prefix_init.sh"
"$SCRIPTS_DIR/20_winetricks.sh"
"$SCRIPTS_DIR/30_mt5_install.sh"
"$SCRIPTS_DIR/35_data_sync.sh"
"$SCRIPTS_DIR/36_myfxbook.sh"
"$SCRIPTS_DIR/40_python_wine.sh"
"$SCRIPTS_DIR/50_python_linux.sh"
"$SCRIPTS_DIR/60_server.sh"

END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))
log INFO "[done] MT5 setup completed in ${ELAPSED}s"
