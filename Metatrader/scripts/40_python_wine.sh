#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# ============================================================
# Wine Python Installation and Package Upgrades
# Always upgrades packages to versions defined in 00_env.sh
# Only fails if upgrade command itself fails
# ============================================================

PYTHON_INSTALLER="/tmp/python-installer.exe"

log INFO "[python-wine] Checking Python installation..."

# Install Python if not present
if ! "$wine_executable" python --version 2>/dev/null; then
    log INFO "[python-wine] Installing Python ${PYTHON_VERSION}..."

    # Get Python installer using prioritized cache
    get_file "python-installer.exe" "$python_url" "$PYTHON_INSTALLER"

    "$wine_executable" "$PYTHON_INSTALLER" /quiet InstallAllUsers=1 PrependPath=1
    rm -f "$PYTHON_INSTALLER"

    # Verify Python was installed
    if ! "$wine_executable" python --version 2>/dev/null; then
        log ERROR "[python-wine] Python installation failed"
        exit 1
    fi
    log INFO "[python-wine] Python installed successfully"
else
    log INFO "[python-wine] Python already installed: $("$wine_executable" python --version 2>&1)"
fi

# Upgrade pip first
log INFO "[python-wine] Upgrading pip..."
"$wine_executable" python -m pip install --upgrade --no-cache-dir pip || log WARN "[python-wine] pip upgrade failed; continuing"

# ============================================================
# PACKAGE UPGRADES - Always upgrade to centralized versions
# Versions defined in 00_env.sh
# ============================================================

log INFO "[python-wine] Upgrading packages to required versions..."
log INFO "[python-wine] Versions: RPYC=${RPYC_VERSION}, PYDANTIC=${PYDANTIC_VERSION}, PLUMBUM=${PLUMBUM_VERSION}, NUMPY=${NUMPY_VERSION}"

# MetaTrader5 - REQUIRED for MT5 API
log INFO "[python-wine] Upgrading MetaTrader5==${MT5_PYPI_VERSION}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade "MetaTrader5==${MT5_PYPI_VERSION}"; then
    log ERROR "[python-wine] MetaTrader5 upgrade failed"
    exit 1
fi

# mt5linux - ALWAYS pull from main branch
log INFO "[python-wine] Upgrading mt5linux from ${MT5LINUX_REPO}@${MT5LINUX_BRANCH}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade --force-reinstall --no-deps "${MT5LINUX_SPEC}"; then
    log ERROR "[python-wine] mt5linux upgrade failed"
    exit 1
fi

# RPyC - required for async compatibility
log INFO "[python-wine] Upgrading ${RPYC_SPEC}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade "${RPYC_SPEC}"; then
    log ERROR "[python-wine] rpyc upgrade failed"
    exit 1
fi

# Pydantic - required for validation
log INFO "[python-wine] Upgrading ${PYDANTIC_SPEC}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade "${PYDANTIC_SPEC}"; then
    log ERROR "[python-wine] pydantic upgrade failed"
    exit 1
fi

# plumbum - required for RPyC compatibility
log INFO "[python-wine] Upgrading ${PLUMBUM_SPEC}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade "${PLUMBUM_SPEC}"; then
    log ERROR "[python-wine] plumbum upgrade failed"
    exit 1
fi

# numpy - required for MT5 compatibility (must be <2 for MT5)
log INFO "[python-wine] Upgrading ${NUMPY_SPEC}..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade "${NUMPY_SPEC}"; then
    log ERROR "[python-wine] numpy upgrade failed"
    exit 1
fi

# python-dateutil - required for datetime handling
log INFO "[python-wine] Upgrading python-dateutil..."
if ! "$wine_executable" python -m pip install --no-cache-dir --upgrade python-dateutil; then
    log ERROR "[python-wine] python-dateutil upgrade failed"
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
