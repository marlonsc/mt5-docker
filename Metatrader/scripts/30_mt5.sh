#!/bin/bash
# MT5 Installation and Configuration
# Downloads and installs LATEST versions at every startup
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# Timeout for MT5 installer (seconds)
MT5_INSTALL_TIMEOUT=60

# ============================================================
# Install MetaTrader5 pip package (LATEST VERSION)
# ============================================================
install_mt5_pip() {
    log INFO "[mt5] Installing MetaTrader5 pip package (latest)..."

    if [ ! -f "$WINE_PYTHON_PATH" ]; then
        log ERROR "[mt5] FATAL: Wine Python not found at $WINE_PYTHON_PATH"
        return 1
    fi

    # Install MetaTrader5 without upgrading numpy (numpy 1.26.4 is Wine-compatible)
    # numpy 2.x uses ucrtbase.dll functions Wine hasn't implemented
    "$wine_executable" "$WINE_PYTHON_PATH" -m pip install --upgrade --no-cache-dir --no-deps \
        MetaTrader5 2>&1 || {
        log ERROR "[mt5] MetaTrader5 pip installation failed"
        return 1
    }

    "$wine_executable" "$WINE_PYTHON_PATH" -c "import MetaTrader5; print(f'MetaTrader5 {MetaTrader5.__version__} installed')" 2>/dev/null || {
        log ERROR "[mt5] MetaTrader5 import verification failed"
        return 1
    }

    # Install mt5linux for the RPyC bridge (latest from GitHub)
    log INFO "[mt5] Installing mt5linux bridge package..."
    "$wine_executable" "$WINE_PYTHON_PATH" -m pip install --upgrade --no-cache-dir \
        'https://github.com/marlonsc/mt5linux/archive/refs/heads/master.tar.gz' 2>&1 || {
        log ERROR "[mt5] mt5linux pip installation failed"
        return 1
    }

    "$wine_executable" "$WINE_PYTHON_PATH" -c "import mt5linux; print('mt5linux bridge installed')" 2>/dev/null || {
        log ERROR "[mt5] mt5linux import verification failed"
        return 1
    }
}

# ============================================================
# Install MetaTrader 5 Terminal (LATEST VERSION)
# Downloads and runs installer - with timeout to handle stuck dialogs
# ============================================================
install_mt5_terminal() {
    # Skip if already installed
    if [ -e "$mt5file" ]; then
        log INFO "[mt5] Terminal already installed: $mt5file"
        return 0
    fi

    log INFO "[mt5] Installing MetaTrader 5 terminal (latest)..."

    MT5_SETUP="/tmp/mt5setup.exe"

    # Download fresh installer for latest version
    log INFO "[mt5] Downloading mt5setup.exe..."
    curl -fSL -o "$MT5_SETUP" "$mt5setup_url" || {
        log ERROR "[mt5] Failed to download mt5setup.exe"
        return 1
    }

    # Run installer with timeout (may get stuck on error dialog)
    log INFO "[mt5] Running installer (timeout: ${MT5_INSTALL_TIMEOUT}s)..."

    # Start installer in background
    "$wine_executable" "$MT5_SETUP" "/auto" &
    INSTALLER_PID=$!

    # Wait for either completion or timeout
    local elapsed=0
    while [ $elapsed -lt $MT5_INSTALL_TIMEOUT ]; do
        # Check if installer finished
        if ! kill -0 $INSTALLER_PID 2>/dev/null; then
            log INFO "[mt5] Installer completed"
            break
        fi

        # Check if terminal64.exe exists (installation succeeded)
        if [ -e "$mt5file" ]; then
            log INFO "[mt5] Terminal detected - killing installer"
            kill $INSTALLER_PID 2>/dev/null || true
            # Also kill any Wine processes related to installer
            pkill -f "mt5setup" 2>/dev/null || true
            wineserver -k 2>/dev/null || true
            sleep 2
            break
        fi

        sleep 5
        elapsed=$((elapsed + 5))
    done

    # Cleanup - kill if still running after timeout
    if kill -0 $INSTALLER_PID 2>/dev/null; then
        log WARN "[mt5] Installer timeout - forcing kill"
        kill $INSTALLER_PID 2>/dev/null || true
        pkill -f "mt5setup" 2>/dev/null || true
        wineserver -k 2>/dev/null || true
        sleep 2
    fi

    rm -f "$MT5_SETUP"

    # Verify installation
    if [ -e "$mt5file" ]; then
        log INFO "[mt5] Terminal installed: $mt5file"
    else
        log ERROR "[mt5] Terminal installation failed - terminal64.exe not found"
        return 1
    fi
}

# ============================================================
# Generate Configuration (if credentials provided)
# Format based on official MT5 documentation and MQL5 forum research
# See: https://www.metatrader5.com/en/terminal/help/start_advanced/start
# ============================================================
generate_config() {
    if [ -z "${MT5_LOGIN:-}" ] || [ -z "${MT5_PASSWORD:-}" ] || [ -z "${MT5_SERVER:-}" ]; then
        log INFO "[mt5] No credentials provided, skipping config generation"
        return 0
    fi

    log INFO "[mt5] Generating config for account ${MT5_LOGIN}@${MT5_SERVER}..."
    mkdir -p "$MT5_CONFIG_DIR"

    # Config format per official MT5 documentation
    cat > "$MT5_STARTUP_INI" << EOF
[Common]
Login=${MT5_LOGIN}
Password=${MT5_PASSWORD}
Server=${MT5_SERVER}
KeepPrivate=1
CertInstall=1
NewsEnable=1
ProxyEnable=0

[Experts]
AllowLiveTrading=1
AllowDllImport=1
Enabled=1
Account=0
Profile=0
EOF

    log INFO "[mt5] Config written to: $MT5_STARTUP_INI"
}

# ============================================================
# Launch MT5
# ============================================================
launch_mt5() {
    if [ ! -e "$mt5file" ]; then
        log ERROR "[mt5] Cannot launch - not installed"
        return 1
    fi

    # Check if already running
    if pgrep -f "terminal64.exe" >/dev/null 2>&1; then
        log INFO "[mt5] Terminal already running"
        return 0
    fi

    log INFO "[mt5] Launching terminal..."

    # Build command line arguments
    # MT5 uses command line args for auto-login (more reliable than config file)
    MT5_ARGS="/portable"

    if [ -n "${MT5_LOGIN:-}" ] && [ -n "${MT5_PASSWORD:-}" ] && [ -n "${MT5_SERVER:-}" ]; then
        log INFO "[mt5] Auto-login enabled for account ${MT5_LOGIN}@${MT5_SERVER}"
        MT5_ARGS="$MT5_ARGS /login:${MT5_LOGIN} /password:${MT5_PASSWORD} /server:${MT5_SERVER}"
    fi

    # Add config file if exists (for other settings like AutoTrading)
    if [ -f "$MT5_STARTUP_INI" ]; then
        MT5_CONFIG_WIN="C:\\Program Files\\MetaTrader 5\\Config\\startup.ini"
        MT5_ARGS="$MT5_ARGS /config:$MT5_CONFIG_WIN"
    fi

    log INFO "[mt5] Starting with args: $MT5_ARGS"
    "$wine_executable" "$mt5file" $MT5_ARGS &

    # Wait for terminal to start
    local waited=0
    while [ $waited -lt 30 ]; do
        if pgrep -f "terminal64.exe" >/dev/null 2>&1; then
            log INFO "[mt5] Terminal started"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done

    log WARN "[mt5] Terminal may not have started"
    return 0
}

# ============================================================
# Main execution
# ============================================================
install_mt5_pip
install_mt5_terminal
generate_config
# NOTE: MT5 terminal is started by svc-mt5server (s6-overlay service)
# Do NOT launch here to avoid duplicate processes
log INFO "[mt5] Setup complete - terminal will be started by svc-mt5server"
