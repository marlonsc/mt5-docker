#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

ARCHIVE_PATH="/data/config.tar.zst"
MARKER_PATH="/config/.config-unpacked"

# Only run once per persistent /config
if [ -f "$MARKER_PATH" ]; then
  log INFO "[config] Already unpacked; skipping"
  exit 0
fi

if [ -f "$ARCHIVE_PATH" ]; then
  log INFO "[config] Unpacking /config from archive $ARCHIVE_PATH"
  mkdir -p /config
  tar --zstd -xpf "$ARCHIVE_PATH" -C / || { log ERROR "[config] Failed to unpack archive"; exit 1; }
  touch "$MARKER_PATH"
  log INFO "[config] Unpack complete"
else
  log INFO "[config] No archive found; skipping"
fi
