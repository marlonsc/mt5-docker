#!/bin/bash
# test-container.sh - Start and validate mt5docker test container
#
# This script starts the ISOLATED test container (mt5docker-test)
# and verifies the RPyC service is ready.
#
# Uses the SAME docker-compose.yaml with .env.test for test-specific values.
#
# Port allocation (to avoid conflicts):
#   - Production:     mt5,             port 8001
#   - neptor tests:   neptor-mt5-test, port 18812
#   - mt5linux tests: mt5linux-test,   port 28812
#   - mt5docker tests: mt5docker-test, port 48812
#
# Usage:
#   ./scripts/test-container.sh         # Start and verify
#   ./scripts/test-container.sh --stop  # Stop test container

set -euo pipefail

# Configuration (defaults, can be overridden by .env.test)
CONTAINER_NAME="${MT5_CONTAINER_NAME:-mt5docker-test}"
RPYC_PORT="${MT5_RPYC_PORT:-48812}"
HEALTH_PORT="${MT5_HEALTH_PORT:-48002}"
VNC_PORT="${MT5_VNC_PORT:-43000}"
TIMEOUT=180  # seconds to wait for RPyC service
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="${PROJECT_DIR}/docker"
ENV_FILE="${PROJECT_DIR}/.env.test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if container is running
is_container_running() {
    docker ps -q -f "name=^${CONTAINER_NAME}$" | grep -q .
}

# Check if RPyC service is ready (actual connection, not just port)
is_rpyc_ready() {
    python3 -c "
from rpyc.utils.classic import connect
try:
    conn = connect('localhost', ${RPYC_PORT})
    conn._config['sync_request_timeout'] = 5
    _ = conn.modules
    conn.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null
}

# Wait for RPyC service
wait_for_rpyc() {
    local start=$(date +%s)
    local elapsed=0

    log_info "Waiting for RPyC service on port ${RPYC_PORT}..."

    while [ $elapsed -lt $TIMEOUT ]; do
        if is_rpyc_ready; then
            log_info "RPyC service ready after ${elapsed}s"
            return 0
        fi
        sleep 3
        elapsed=$(($(date +%s) - start))
        echo -ne "\r  Waiting... ${elapsed}/${TIMEOUT}s"
    done

    echo ""
    log_error "RPyC service not ready after ${TIMEOUT}s"
    return 1
}

# Stop container
stop_container() {
    log_info "Stopping test container..."
    docker compose -f "$DOCKER_DIR/compose.yaml" --project-name mt5docker-test --env-file "$ENV_FILE" down
    log_info "Test container stopped"
}

# Check for env files and load configuration
check_env_file() {
    # Load main .env for credentials (required)
    if [ ! -f "${PROJECT_DIR}/.env" ]; then
        log_error ".env file not found - credentials required"
        return 1
    fi
    set -a
    source "${PROJECT_DIR}/.env"
    set +a

    # Load .env.test for test container settings (optional overrides)
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        log_info "Test config loaded from .env.test (container settings only)"
    else
        log_warn ".env.test not found, using default test ports"
    fi

    # Update local variables from env
    CONTAINER_NAME="${MT5_CONTAINER_NAME:-mt5docker-test}"
    RPYC_PORT="${MT5_RPYC_PORT:-48812}"
    HEALTH_PORT="${MT5_HEALTH_PORT:-48002}"
    VNC_PORT="${MT5_VNC_PORT:-43000}"

    # Verify credentials from .env (not .env.test)
    if [ -z "${MT5_LOGIN:-}" ] || [ "$MT5_LOGIN" = "your_login_number" ]; then
        log_error "MT5_LOGIN not configured in .env"
        return 1
    fi
    if [ -z "${MT5_PASSWORD:-}" ] || [ "$MT5_PASSWORD" = "your_password" ]; then
        log_error "MT5_PASSWORD not configured in .env"
        return 1
    fi

    log_info "Credentials loaded from .env"
    return 0
}

# Start container
start_container() {
    # Check .env.test file first
    if ! check_env_file; then
        return 1
    fi

    # Check if already running
    if is_container_running; then
        if is_rpyc_ready; then
            log_info "Test container already running and healthy"
            return 0
        fi
        log_warn "Container running but RPyC not responding. Restarting..."
        docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    fi

    log_info "Starting test container: ${CONTAINER_NAME}"
    log_info "  RPyC port: ${RPYC_PORT}"
    log_info "  Health port: ${HEALTH_PORT}"
    log_info "  VNC port: ${VNC_PORT}"

    # Start with test env file
    docker compose -f "$DOCKER_DIR/compose.yaml" --project-name mt5docker-test --env-file "$ENV_FILE" up -d

    # Wait for service
    if ! wait_for_rpyc; then
        log_error "Failed to start test container"
        docker logs "$CONTAINER_NAME" --tail 50
        return 1
    fi

    log_info "Test container ready!"
    echo ""
    log_info "Connection info:"
    echo "  RPyC:   localhost:${RPYC_PORT}"
    echo "  Health: localhost:${HEALTH_PORT}"
    echo "  VNC:    http://localhost:${VNC_PORT}"
}

# Main
case "${1:-start}" in
    --stop|-s|stop)
        stop_container
        ;;
    --help|-h|help)
        echo "Usage: $0 [--stop|--help]"
        echo ""
        echo "Start and validate mt5docker test container."
        echo ""
        echo "Options:"
        echo "  --stop   Stop the test container"
        echo "  --help   Show this help"
        ;;
    *)
        start_container
        ;;
esac
