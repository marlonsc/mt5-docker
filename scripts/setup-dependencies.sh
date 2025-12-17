#!/bin/bash
# =============================================================================
# Setup dependencies for mt5docker
# =============================================================================
# This script configures mt5linux dependency based on environment:
#
# - pyproject.toml uses git reference by default (for CI/Dependabot)
# - This script overrides with local path when in development environment
#
# Features:
# - Idempotent: Safe to run multiple times
# - Resilient: Handles edge cases and errors gracefully
# - Auto-detects: Development vs CI/Production environment
#
# Usage:
#   ./setup-dependencies.sh           # Auto-detect and configure
#   ./setup-dependencies.sh --force   # Force reinstall even if already installed
#   ./setup-dependencies.sh --check   # Check current state without changes
#   ./setup-dependencies.sh --help    # Show help
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# mt5linux paths
readonly MT5LINUX_LOCAL_PATH="${MT5LINUX_LOCAL_PATH:-$PROJECT_ROOT/../mt5linux}"
readonly MT5LINUX_PACKAGE_NAME="mt5linux"

# Colors (disabled if not a terminal)
if [[ -t 1 ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly NC='\033[0m'
else
    readonly RED=''
    readonly GREEN=''
    readonly YELLOW=''
    readonly BLUE=''
    readonly NC=''
fi

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

log_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

log_error() {
    echo -e "${RED}✗ ${NC}$1" >&2
}

show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Configure mt5linux dependency for mt5docker project.

Options:
    --force     Force reinstall even if already installed correctly
    --check     Check current state without making changes
    --help      Show this help message

Environment Variables:
    MT5LINUX_LOCAL_PATH    Override local mt5linux path (default: ../mt5linux)

Examples:
    $SCRIPT_NAME              # Auto-detect and configure
    $SCRIPT_NAME --check      # Check without changes
    $SCRIPT_NAME --force      # Force reinstall

EOF
}

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Get the installed location of mt5linux (if any)
get_mt5linux_location() {
    python3 -c "
import importlib.util
spec = importlib.util.find_spec('$MT5LINUX_PACKAGE_NAME')
if spec and spec.origin:
    print(spec.origin)
" 2>/dev/null || true
}

# Check if mt5linux is installed as editable from local path
is_local_editable_install() {
    local location
    location="$(get_mt5linux_location)"

    if [[ -z "$location" ]]; then
        return 1
    fi

    # Resolve both paths to absolute for comparison
    local resolved_local
    resolved_local="$(cd "$MT5LINUX_LOCAL_PATH" 2>/dev/null && pwd)" || return 1

    # Check if installed location is within the local path
    [[ "$location" == "$resolved_local"* ]]
}

# Check if mt5linux is installed from git/pypi
is_git_install() {
    local location
    location="$(get_mt5linux_location)"

    if [[ -z "$location" ]]; then
        return 1
    fi

    # If it's in site-packages and not in our local path, it's from git/pypi
    [[ "$location" == *"site-packages"* ]]
}

# Validate local mt5linux directory
validate_local_path() {
    local path="$1"

    if [[ ! -d "$path" ]]; then
        return 1
    fi

    # Check for valid Python package (pyproject.toml or setup.py)
    if [[ -f "$path/pyproject.toml" ]] || [[ -f "$path/setup.py" ]]; then
        return 0
    fi

    return 1
}

# Get mt5linux version
get_mt5linux_version() {
    python3 -c "
try:
    import mt5linux
    print(getattr(mt5linux, '__version__', 'unknown'))
except ImportError:
    print('not installed')
" 2>/dev/null || echo "error"
}

# =============================================================================
# Main Functions
# =============================================================================

check_prerequisites() {
    local missing=()

    if ! command_exists python3; then
        missing+=("python3")
    fi

    if ! command_exists pip3 && ! command_exists pip; then
        missing+=("pip")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        exit 1
    fi
}

show_status() {
    log_info "Current mt5linux status:"

    local version
    version="$(get_mt5linux_version)"
    echo "  Version: $version"

    local location
    location="$(get_mt5linux_location)"
    if [[ -n "$location" ]]; then
        echo "  Location: $location"
    fi

    if is_local_editable_install; then
        echo "  Mode: Local editable (development)"
    elif is_git_install; then
        echo "  Mode: Git/PyPI (production)"
    else
        echo "  Mode: Not installed"
    fi

    echo ""
    if [[ -d "$MT5LINUX_LOCAL_PATH" ]]; then
        log_info "Local mt5linux found at: $(cd "$MT5LINUX_LOCAL_PATH" && pwd)"
    else
        log_info "Local mt5linux not found (path: $MT5LINUX_LOCAL_PATH)"
    fi
}

install_local_editable() {
    local local_path="$1"
    local force="${2:-false}"

    # Check if already installed correctly (idempotent)
    if [[ "$force" != "true" ]] && is_local_editable_install; then
        log_success "mt5linux already installed as local editable - skipping (use --force to reinstall)"
        return 0
    fi

    log_info "Installing mt5linux from local path: $local_path"

    # Use pip to install editable
    # --no-deps: Don't install dependencies (they're managed by poetry)
    # --force-reinstall: Ensure we override any existing installation
    if pip3 install -e "$local_path" --no-deps --force-reinstall --quiet 2>/dev/null || \
       pip install -e "$local_path" --no-deps --force-reinstall --quiet 2>/dev/null; then
        log_success "Local mt5linux installed (editable mode)"
    else
        log_error "Failed to install local mt5linux"
        return 1
    fi

    # Verify installation
    if is_local_editable_install; then
        log_success "Verified: mt5linux is now using local path"
        log_warning "Note: Changes to $local_path will be reflected immediately"
    else
        log_error "Installation verification failed"
        return 1
    fi
}

# =============================================================================
# Main Entry Point
# =============================================================================

main() {
    local force=false
    local check_only=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force)
                force=true
                shift
                ;;
            --check)
                check_only=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Check prerequisites
    check_prerequisites

    # Check-only mode
    if [[ "$check_only" == "true" ]]; then
        show_status
        exit 0
    fi

    echo ""
    log_info "Configuring mt5linux dependency..."
    echo ""

    # Check if local mt5linux exists and is valid
    if validate_local_path "$MT5LINUX_LOCAL_PATH"; then
        log_info "Development environment detected"
        install_local_editable "$MT5LINUX_LOCAL_PATH" "$force"
    else
        log_info "CI/Production environment detected"
        log_success "Using mt5linux from GitHub (configured in pyproject.toml)"

        if is_git_install; then
            log_success "mt5linux is already installed from Git"
        else
            log_warning "Run 'poetry install' to install dependencies"
        fi
    fi

    echo ""
    show_status
}

# Run main function
main "$@"
