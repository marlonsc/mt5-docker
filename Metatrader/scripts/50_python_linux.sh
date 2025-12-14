#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# mt5linux GitHub repository (fallback)
MT5LINUX_REPO="git+https://github.com/marlonsc/mt5linux.git@master"

# Local mount path (used by docker-compose.test.yaml for workspace projects)
MT5LINUX_LOCAL="/opt/mt5linux-local"

log INFO "[8/9] Checking mt5linux library in Linux"

# Priority 1: Check if local mt5linux is mounted (workspace project)
if [ -d "$MT5LINUX_LOCAL" ] && [ -f "$MT5LINUX_LOCAL/__init__.py" ]; then
    log INFO "[8/9] Found local mt5linux at $MT5LINUX_LOCAL"

    # Uninstall pip version to avoid conflicts (PYTHONPATH alone doesn't work)
    if is_python_package_installed "mt5linux"; then
        log INFO "[8/9] Uninstalling pip mt5linux to use local version"
        pip3 uninstall -y mt5linux 2>/dev/null || true
    fi

    # Add to PYTHONPATH for this session and future sessions
    export PYTHONPATH="${MT5LINUX_LOCAL}:${PYTHONPATH:-}"
    echo "export PYTHONPATH=\"${MT5LINUX_LOCAL}:\${PYTHONPATH:-}\"" > /etc/profile.d/mt5linux.sh

    # Install dependencies only (mt5linux code comes from mount)
    pip3 install --break-system-packages --no-cache-dir \
        "numpy>=2.1.0" "rpyc>=5.2.0,<6.0.0" "plumbum>=1.8.0" "pyparsing>=3.0.0" || {
        log ERROR "[8/9] Failed to install mt5linux dependencies"
        exit 1
    }

    # Verify local installation works
    MT5_VERSION=$(PYTHONPATH="$MT5LINUX_LOCAL" python3 -c "import mt5linux; print(getattr(mt5linux, '__version__', 'local'))" 2>/dev/null || echo "local-mount")
    log INFO "[8/9] Using LOCAL mt5linux from workspace (version: $MT5_VERSION)"

# Priority 2: Install from GitHub if not installed
elif ! is_python_package_installed "mt5linux"; then
    log INFO "[8/9] Installing mt5linux from GitHub (marlonsc/mt5linux)"

    # Install dependencies first
    pip3 install --break-system-packages --no-cache-dir \
        "numpy>=2.1.0" "rpyc>=5.2.0,<6.0.0" "plumbum>=1.8.0" "pyparsing>=3.0.0" || {
        log ERROR "[8/9] Failed to install mt5linux dependencies"
        exit 1
    }

    # Install mt5linux from GitHub
    pip3 install --break-system-packages --no-cache-dir "$MT5LINUX_REPO" || {
        log ERROR "[8/9] Failed to install mt5linux from GitHub"
        exit 1
    }

    # Verify installation
    MT5_VERSION=$(python3 -c "import mt5linux; print(getattr(mt5linux, '__version__', '0.2.1'))" 2>/dev/null || echo "unknown")
    log INFO "[8/9] mt5linux installed from GitHub (version: $MT5_VERSION)"

# Priority 3: Already installed
else
    MT5_VERSION=$(python3 -c "import mt5linux; print(getattr(mt5linux, '__version__', '0.2.1'))" 2>/dev/null || echo "unknown")
    log INFO "[8/9] mt5linux already installed (version: $MT5_VERSION)"
fi

log INFO "[8/9] Checking and installing pyxdg library in Linux"
if ! is_python_package_installed "pyxdg"; then
    log INFO "[8/9] Installing pyxdg"
    pip3 install --break-system-packages --no-cache-dir pyxdg || {
        log ERROR "[8/9] Failed to install pyxdg"
        exit 1
    }
else
    log INFO "[8/9] pyxdg already installed"
fi
