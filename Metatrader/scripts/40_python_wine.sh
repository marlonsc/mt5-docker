#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# ============================================================
# Wine Python Installation and Package Upgrades
# - Upgrades Python if version doesn't match PYTHON_VERSION
# - Always upgrades packages to versions defined in 00_env.sh
# - Only fails if upgrade command itself fails
# ============================================================

PYTHON_INSTALLER="/tmp/python-installer.exe"

# Extract major.minor version (e.g., "3.13" from "3.13.11")
REQUIRED_PYTHON_MAJOR_MINOR="${PYTHON_VERSION%.*}"

log INFO "[python-wine] Required Python: ${PYTHON_VERSION} (${REQUIRED_PYTHON_MAJOR_MINOR}.x)"

# ============================================================
# Check and upgrade Python if needed
# ============================================================
upgrade_python_if_needed() {
    local current_version
    local current_major_minor

    if "$wine_executable" python --version 2>/dev/null; then
        current_version=$("$wine_executable" python --version 2>&1 | sed 's/Python //')
        current_major_minor="${current_version%.*}"
        log INFO "[python-wine] Current Python: ${current_version} (${current_major_minor}.x)"

        if [ "$current_major_minor" = "$REQUIRED_PYTHON_MAJOR_MINOR" ]; then
            log INFO "[python-wine] Python version OK"
            return 0
        fi

        log INFO "[python-wine] Python version mismatch. Upgrading ${current_version} -> ${PYTHON_VERSION}..."

        # Uninstall old Python silently
        log INFO "[python-wine] Uninstalling old Python..."
        local old_installer="/tmp/old-python-installer.exe"

        # Try to find and run uninstaller, or just proceed with new install
        if [ -f "$WINEPREFIX/drive_c/Program Files/Python${current_major_minor//./}/unins000.exe" ]; then
            "$wine_executable" "$WINEPREFIX/drive_c/Program Files/Python${current_major_minor//./}/unins000.exe" /SILENT /VERYSILENT 2>/dev/null || true
        fi

        # Remove Python directories to ensure clean install
        rm -rf "$WINEPREFIX/drive_c/Program Files/Python"* 2>/dev/null || true
        rm -rf "$WINEPREFIX/drive_c/users/*/AppData/Local/Programs/Python"* 2>/dev/null || true
    else
        log INFO "[python-wine] Python not installed"
    fi

    # Install required Python version
    log INFO "[python-wine] Installing Python ${PYTHON_VERSION}..."
    get_file "python-installer.exe" "$python_url" "$PYTHON_INSTALLER"

    if ! "$wine_executable" "$PYTHON_INSTALLER" /quiet /passive InstallAllUsers=1 PrependPath=1 Include_pip=1 2>/dev/null; then
        log ERROR "[python-wine] Python installation failed"
        rm -f "$PYTHON_INSTALLER"
        exit 1
    fi
    rm -f "$PYTHON_INSTALLER"

    # Verify installation
    if ! "$wine_executable" python --version 2>/dev/null; then
        log ERROR "[python-wine] Python installation verification failed"
        exit 1
    fi

    local installed_version
    installed_version=$("$wine_executable" python --version 2>&1 | sed 's/Python //')
    log INFO "[python-wine] Python ${installed_version} installed successfully"
}

# Run Python upgrade check
upgrade_python_if_needed

# Upgrade pip first
log INFO "[python-wine] Upgrading pip..."
"$wine_executable" python -m pip install --upgrade --no-cache-dir --quiet pip || log WARN "[python-wine] pip upgrade failed; continuing"

# ============================================================
# PACKAGE UPGRADES - Always upgrade to centralized versions
# Versions defined in 00_env.sh
# ============================================================

log INFO "[python-wine] Upgrading packages to required versions..."
log INFO "[python-wine] Versions: RPYC=${RPYC_VERSION}, PYDANTIC=${PYDANTIC_VERSION}, PLUMBUM=${PLUMBUM_VERSION}, NUMPY=${NUMPY_VERSION}"

# MetaTrader5 - REQUIRED for MT5 API (always upgrade)
log INFO "[python-wine] Upgrading MetaTrader5==${MT5_PYPI_VERSION}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade --quiet "MetaTrader5==${MT5_PYPI_VERSION}"; then
    log ERROR "[python-wine] MetaTrader5 upgrade failed"
    exit 1
fi

# RPyC - required for async compatibility
log INFO "[python-wine] Upgrading ${RPYC_SPEC}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade --quiet "${RPYC_SPEC}"; then
    log ERROR "[python-wine] rpyc upgrade failed"
    exit 1
fi

# Pydantic - required for validation
log INFO "[python-wine] Upgrading ${PYDANTIC_SPEC}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade --quiet "${PYDANTIC_SPEC}"; then
    log ERROR "[python-wine] pydantic upgrade failed"
    exit 1
fi

# plumbum - required for RPyC compatibility
log INFO "[python-wine] Upgrading ${PLUMBUM_SPEC}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade --quiet "${PLUMBUM_SPEC}"; then
    log ERROR "[python-wine] plumbum upgrade failed"
    exit 1
fi

# numpy - required for MT5 compatibility (must be >=2.1 for modern MT5)
log INFO "[python-wine] Upgrading ${NUMPY_SPEC}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade --quiet "${NUMPY_SPEC}"; then
    log ERROR "[python-wine] numpy upgrade failed"
    exit 1
fi

# python-dateutil - required for datetime handling
log INFO "[python-wine] Upgrading python-dateutil..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade --quiet python-dateutil; then
    log ERROR "[python-wine] python-dateutil upgrade failed"
    exit 1
fi

# structlog - required for mt5linux logging
log INFO "[python-wine] Upgrading structlog..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade --quiet "structlog>=25.5.0"; then
    log ERROR "[python-wine] structlog upgrade failed"
    exit 1
fi

# mt5linux - ALWAYS pull from main branch (force reinstall)
# Install AFTER all dependencies (rpyc, pydantic, plumbum, numpy, structlog)
log INFO "[python-wine] Upgrading mt5linux from ${MT5LINUX_REPO}@${MT5LINUX_BRANCH}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade --force-reinstall --no-deps --quiet "${MT5LINUX_SPEC}"; then
    log ERROR "[python-wine] mt5linux upgrade failed"
    exit 1
fi

# ============================================================
# VERIFICATION - Ensure critical packages can be imported
# ============================================================

log INFO "[python-wine] Verifying package imports..."
if ! "$wine_executable" python -c "import MetaTrader5" 2>/dev/null; then
    log ERROR "[python-wine] MetaTrader5 import verification failed"
    exit 1
fi
if ! "$wine_executable" python -c "import rpyc; print(f'rpyc {rpyc.__version__}')" 2>/dev/null; then
    log ERROR "[python-wine] rpyc import verification failed"
    exit 1
fi
if ! "$wine_executable" python -c "import pydantic; print(f'pydantic {pydantic.__version__}')" 2>/dev/null; then
    log ERROR "[python-wine] pydantic import verification failed"
    exit 1
fi

log INFO "[python-wine] All packages upgraded and verified successfully"
