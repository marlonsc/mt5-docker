#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

MT5_SETUP="$WINEPREFIX/drive_c/mt5setup.exe"

if [ -e "$mt5file" ]; then
    log INFO "[3/9] MetaTrader 5 already installed at $mt5file"
else
    log INFO "[3/9] MetaTrader 5 not found. Installing..."

    # Set Windows version to Win10
    "$wine_executable" reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win10" /f

    # Get MT5 installer using prioritized cache
    log INFO "[3/9] Getting MT5 installer..."
    get_file "mt5setup.exe" "$mt5setup_url" "$MT5_SETUP"

    # Install MT5
    log INFO "[3/9] Installing MetaTrader 5..."
    "$wine_executable" "$MT5_SETUP" "/auto" &
    wait || true

    # Cleanup installer
    rm -f "$MT5_SETUP"
fi

# Verify installation and run
if [ -e "$mt5file" ]; then
    log INFO "[3/9] MetaTrader 5 installed successfully. Running MT5..."

    # Build MT5 launch arguments
    MT5_ARGS="/portable"  # Always use portable mode for Docker
    MT5_CONFIG_DIR="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/Config"
    MT5_STARTUP_INI="$MT5_CONFIG_DIR/startup.ini"

    # Use config file if available (created by 31_mt5_config.sh)
    if [ -f "$MT5_STARTUP_INI" ]; then
        MT5_ARGS="$MT5_ARGS /config:\"C:\\Program Files\\MetaTrader 5\\Config\\startup.ini\""
        log INFO "[3/9] Using config file for auto-login"
    elif [ -n "${MT5_LOGIN:-}" ] && [ -n "${MT5_PASSWORD:-}" ] && [ -n "${MT5_SERVER:-}" ]; then
        # Fallback to command line arguments
        MT5_ARGS="$MT5_ARGS /login:${MT5_LOGIN} /password:${MT5_PASSWORD} /server:${MT5_SERVER}"
        log INFO "[3/9] Using command line args for auto-login (account ${MT5_LOGIN})"
    else
        log INFO "[3/9] No auto-login configured (set MT5_LOGIN, MT5_PASSWORD, MT5_SERVER)"
    fi

    # Launch MT5 in portable mode with config
    log INFO "[3/9] Starting MT5: $MT5_ARGS"
    "$wine_executable" "$mt5file" $MT5_ARGS &

    # Wait for MT5 to initialize
    sleep 5
else
    log ERROR "[3/9] MetaTrader 5 installation failed. File not found: $mt5file"
fi
