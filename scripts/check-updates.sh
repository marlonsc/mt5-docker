#!/bin/bash
# MT5 Docker - Check for dependency updates
# Run this periodically to check for new versions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VERSIONS_FILE="$ROOT_DIR/versions.env"

echo "=========================================="
echo "MT5 Docker - Dependency Update Check"
echo "=========================================="
echo ""

# Load current versions
if [ -f "$VERSIONS_FILE" ]; then
    # shellcheck source=/dev/null
    source "$VERSIONS_FILE"
else
    echo "Warning: $VERSIONS_FILE not found"
fi

CURRENT_PYTHON="${PYTHON_VERSION:-unknown}"
CURRENT_GECKO="${GECKO_VERSION:-unknown}"
CURRENT_MT5_PYPI="${MT5_PYPI_VERSION:-unknown}"

UPDATES_AVAILABLE=0

# Check MetaTrader5 PyPI version
echo "MetaTrader5 (PyPI):"
echo "  Current: $CURRENT_MT5_PYPI"
LATEST_MT5_PYPI=$(curl -s "https://pypi.org/pypi/MetaTrader5/json" 2>/dev/null | \
    python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])" 2>/dev/null || echo "error")
echo "  Latest:  $LATEST_MT5_PYPI"
if [ "$LATEST_MT5_PYPI" != "$CURRENT_MT5_PYPI" ] && [ "$LATEST_MT5_PYPI" != "error" ]; then
    echo "  [UPDATE AVAILABLE]"
    UPDATES_AVAILABLE=1
else
    echo "  [up to date]"
fi
echo ""

# Check Python 3.12.x versions
echo "Python 3.12:"
echo "  Current: $CURRENT_PYTHON"
LATEST_PYTHON=$(curl -s "https://www.python.org/ftp/python/" 2>/dev/null | \
    grep -oP '3\.12\.\d+' | sort -V | tail -1 || echo "error")
echo "  Latest:  $LATEST_PYTHON"
if [ "$LATEST_PYTHON" != "$CURRENT_PYTHON" ] && [ "$LATEST_PYTHON" != "error" ] && [ -n "$LATEST_PYTHON" ]; then
    echo "  [UPDATE AVAILABLE]"
    UPDATES_AVAILABLE=1
else
    echo "  [up to date]"
fi
echo ""

# Check Wine Gecko version
echo "Wine Gecko:"
echo "  Current: $CURRENT_GECKO"
LATEST_GECKO=$(curl -s "https://dl.winehq.org/wine/wine-gecko/" 2>/dev/null | \
    grep -oP '\d+\.\d+\.\d+' | sort -V | tail -1 || echo "error")
echo "  Latest:  $LATEST_GECKO"
if [ "$LATEST_GECKO" != "$CURRENT_GECKO" ] && [ "$LATEST_GECKO" != "error" ] && [ -n "$LATEST_GECKO" ]; then
    echo "  [UPDATE AVAILABLE]"
    UPDATES_AVAILABLE=1
else
    echo "  [up to date]"
fi
echo ""

echo "=========================================="
if [ "$UPDATES_AVAILABLE" -eq 1 ]; then
    echo "Updates available! To apply:"
    echo ""
    echo "1. Edit versions.env with new versions"
    echo "2. Rebuild: DOCKER_BUILDKIT=1 docker compose build --no-cache"
    echo "3. Restart: docker compose up -d"
    echo ""
    echo "Quick update commands:"
    if [ "$LATEST_MT5_PYPI" != "$CURRENT_MT5_PYPI" ] && [ "$LATEST_MT5_PYPI" != "error" ]; then
        echo "  sed -i 's/MT5_PYPI_VERSION=.*/MT5_PYPI_VERSION=$LATEST_MT5_PYPI/' versions.env"
    fi
    if [ "$LATEST_PYTHON" != "$CURRENT_PYTHON" ] && [ "$LATEST_PYTHON" != "error" ] && [ -n "$LATEST_PYTHON" ]; then
        echo "  sed -i 's/PYTHON_VERSION=.*/PYTHON_VERSION=$LATEST_PYTHON/' versions.env"
    fi
    if [ "$LATEST_GECKO" != "$CURRENT_GECKO" ] && [ "$LATEST_GECKO" != "error" ] && [ -n "$LATEST_GECKO" ]; then
        echo "  sed -i 's/GECKO_VERSION=.*/GECKO_VERSION=$LATEST_GECKO/' versions.env"
    fi
else
    echo "All dependencies are up to date!"
fi
echo "=========================================="
