#!/bin/bash
# MT5 Auto-Login via Python API
# This script waits for MT5 to start and then logs in programmatically
# Uses both .ini config AND Python API for maximum reliability
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# Skip if no credentials provided
if [ -z "${MT5_LOGIN:-}" ] || [ -z "${MT5_PASSWORD:-}" ] || [ -z "${MT5_SERVER:-}" ]; then
    log INFO "[3.2/9] No MT5 credentials provided; skipping auto-login"
    exit 0
fi

log INFO "[3.2/9] Waiting for MT5 terminal to initialize..."

# Wait for MT5 terminal to start (max 90 seconds)
MAX_WAIT=90
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if pgrep -f "terminal64.exe" > /dev/null 2>&1; then
        log INFO "[3.2/9] MT5 terminal detected, waiting for full initialization..."
        sleep 15  # Give MT5 time to fully initialize and connect to server
        break
    fi
    sleep 3
    WAITED=$((WAITED + 3))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    log ERROR "[3.2/9] MT5 terminal did not start within ${MAX_WAIT}s"
    exit 1
fi

# MT5 executable path for Python API
MT5_PATH="C:\\\\Program Files\\\\MetaTrader 5\\\\terminal64.exe"

# Use Wine Python to login via MetaTrader5 API
log INFO "[3.2/9] Attempting Python API login for account ${MT5_LOGIN} on ${MT5_SERVER}..."

"$wine_executable" python -c "
import MetaTrader5 as mt5
import sys
import time

# Credentials
login = int('${MT5_LOGIN}')
password = '${MT5_PASSWORD}'
server = '${MT5_SERVER}'
path = r'${MT5_PATH}'

print(f'MT5 Python API Login')
print(f'  Path: {path}')
print(f'  Server: {server}')
print(f'  Account: {login}')
print()

# Try multiple times as MT5 might still be initializing
max_attempts = 10
for attempt in range(max_attempts):
    print(f'Attempt {attempt + 1}/{max_attempts}...')

    # Initialize with full parameters
    result = mt5.initialize(
        path=path,
        login=login,
        password=password,
        server=server,
        timeout=30000,  # 30 second timeout
        portable=True   # Use portable mode
    )

    if result:
        account = mt5.account_info()
        if account and account.login > 0:
            print()
            print('=' * 50)
            print('SUCCESS: MT5 Login Successful!')
            print('=' * 50)
            print(f'  Account: {account.login}')
            print(f'  Server: {account.server}')
            print(f'  Name: {account.name}')
            print(f'  Balance: {account.balance} {account.currency}')
            print(f'  Leverage: 1:{account.leverage}')
            print(f'  Trade Mode: {account.trade_mode}')
            print('=' * 50)

            # Keep connection alive - don't shutdown
            sys.exit(0)
        else:
            error = mt5.last_error()
            print(f'  Initialized but no account: {error}')
    else:
        error = mt5.last_error()
        print(f'  Failed: {error}')

    mt5.shutdown()
    time.sleep(5)

print()
print('FAILED: Could not login after all attempts')
print('Please check:')
print('  1. Credentials are correct')
print('  2. Server name matches exactly')
print('  3. MT5 terminal can reach the server')
sys.exit(1)
" 2>&1

LOGIN_RESULT=$?
if [ $LOGIN_RESULT -eq 0 ]; then
    log INFO "[3.2/9] Auto-login successful via Python API"

    # Create marker file to indicate successful login
    touch "$WINEPREFIX/.mt5-logged-in"
else
    log WARN "[3.2/9] Auto-login failed (code: $LOGIN_RESULT)"
    log WARN "[3.2/9] You may need to login manually via VNC (http://localhost:3000)"
fi
