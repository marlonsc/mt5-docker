#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

if [ -e "$mt5file" ]; then
    log INFO "[2/7] File $mt5file already exists."
else
    log INFO "[2/7] File $mt5file is not installed. Installing..."
    "$wine_executable" reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win10" /f
    log INFO "[3/7] Downloading MT5 installer..."
    curl -o "$WINEPREFIX/drive_c/mt5setup.exe" "$mt5setup_url"
    log INFO "[3/7] Installing MetaTrader 5..."
    "$wine_executable" "$WINEPREFIX/drive_c/mt5setup.exe" "/auto" &
    wait || true
    rm -f "$WINEPREFIX/drive_c/mt5setup.exe"
fi

if [ -e "$mt5file" ]; then
    log INFO "[4/7] File $mt5file is installed. Running MT5..."
    "$wine_executable" "$mt5file" &
else
    log ERROR "[4/7] File $mt5file is not installed. MT5 cannot be run."
fi