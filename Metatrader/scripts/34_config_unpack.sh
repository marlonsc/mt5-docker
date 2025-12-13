#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

ARCHIVE_PATH="/data/config.tar.zst"
MARKER_PATH="/config/.config-unpacked"

# Only run once per persistent /config
if [ -f "$MARKER_PATH" ]; then
  log INFO "Config already unpacked; skipping"
  exit 0
fi

if [ -f "$ARCHIVE_PATH" ]; then
  log INFO "Unpacking full /config from archive $ARCHIVE_PATH before any setup"
  mkdir -p /config
  # Extract the tarball which contains top-level 'config/' directory into /
  tar --zstd -xpf "$ARCHIVE_PATH" -C / || { log ERROR "Failed to unpack config archive"; exit 1; }
  touch "$MARKER_PATH"
  log INFO "Config unpack complete"
else
  log INFO "No config archive found at $ARCHIVE_PATH; skipping"
fi
