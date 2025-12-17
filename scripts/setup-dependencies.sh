#!/bin/bash
# Setup dependencies for mt5docker
# This script configures mt5linux dependency based on environment

set -e

# Check if we're in development environment (mt5linux directory exists)
if [ -d "../mt5linux" ]; then
    echo "Development environment detected. Using local mt5linux path dependency."
    # Already configured for local development in pyproject.toml
    exit 0
fi

# Production environment - need to configure git dependency
echo "Production environment detected. Configuring mt5linux git dependency."

# Check if MT5LINUX_REPO is set, otherwise use default
MT5LINUX_REPO="${MT5LINUX_REPO:-https://github.com/marlonsc/mt5linux.git}"

echo "Using mt5linux from: $MT5LINUX_REPO"

# Use poetry to add the git dependency
poetry remove mt5linux --group dev || true
poetry add "mt5linux@{git = \"$MT5LINUX_REPO\", rev = \"main\"}"

echo "Dependencies configured successfully."
echo "Run 'poetry install' to install dependencies."
