#!/bin/bash
set -x

# Configuration variables
mt5file='/config/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe'
export WINEPREFIX='/config/.wine'
export WINEARCH=win64
export W_CACHE="/config/.winetricks-cache"

wine_executable="wine"
metatrader_version="5.0.4993"
mt5server_port="8001"

# Directory for persistent downloads and cache (mounted as a Docker volume)
DOWNLOAD_DIR="/downloads"
mkdir -p "$DOWNLOAD_DIR"
# All installer files, pip cache, and winetricks cache are stored here and never deleted unless outdated.

# Set pip and winetricks cache to persistent download/cache directory
export PIP_CACHE_DIR="$DOWNLOAD_DIR/pip-cache"
export W_CACHE="$DOWNLOAD_DIR/winetricks-cache"
export WINETRICKS_CACHE="$W_CACHE"
mkdir -p "$PIP_CACHE_DIR" "$W_CACHE"

mkdir -p /config/.cache/
mkdir -p /config/.wine/drive_c/

# Version variables for all installers
MONO_VERSION="9.4.0"
GECKO_VERSION="2.47.4"
MT5_VERSION="5.0.4993"
GIT_VERSION="2.45.1"
PYTHON_VERSION="3.12.10"

# URL variables constructed from version variables
gecko_url="https://dl.winehq.org/wine/wine-gecko/${GECKO_VERSION}/wine-gecko-${GECKO_VERSION}-x86_64.msi"
git_url="https://github.com/git-for-windows/git/releases/download/v${GIT_VERSION}.windows.1/Git-${GIT_VERSION}-64-bit.exe"
mono_url="https://dl.winehq.org/wine/wine-mono/${MONO_VERSION}/wine-mono-${MONO_VERSION}-x86.msi"
mt5setup_url="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
python_url="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe"
mt5linux_pip="mt5linux@git+https://github.com/marlonsc/mt5linux.git@master"
lnx_pip_opts="--break-system-packages"
win_pip_opts=""

# Helper: Validate versioned cache file
# Params: $1=file, $2=expected_version_string
validate_cache_file() {
    local file="$1"
    local version="$2"
    local version_file="${file}.version"
    if [ -f "$file" ] && [ -f "$version_file" ]; then
        if grep -Fxq "$version" "$version_file"; then
            return 0
        else
            rm -f "$file" "$version_file"
            return 1
        fi
    else
        rm -f "$file" "$version_file"
        return 1
    fi
}

# Function to display a graphical message
show_message() {
    echo "$1"
}

# Function to check if a dependency is installed
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "$1 is not installed. Please install it to continue."
        exit 1
    fi
}

# Function to check if a Python package is installed
is_python_package_installed() {
    python3 -c "import pkg_resources; exit(not pkg_resources.require('$1'))" 2>/dev/null
    return $?
}

# Function to check if a Python package is installed in Wine
is_wine_python_package_installed() {
    $wine_executable python -c "import pkg_resources; exit(not pkg_resources.require('$1'))" 2>/dev/null
    return $?
}

# Function to check if Wine Gecko is installed
is_wine_gecko_installed() {
    # Wine Gecko is typically registered in the Wine registry under 'Wine Gecko' key
    # This function checks for the presence of the Gecko DLL in the Wine system directory
    # Adjust path as needed for different Wine versions or architectures
    if [ -f "$WINEPREFIX/drive_c/windows/system32/gecko/2.47.4/wine_gecko-2.47.4-x86_64.msi" ]; then
        return 0
    else
        return 1
    fi
}

# Check for necessary dependencies
check_dependency "curl"
check_dependency "$wine_executable"

# Mono download and install
MONO_MSI="$DOWNLOAD_DIR/mono-${MONO_VERSION}.msi"
if [ ! -e "/config/.wine/drive_c/windows/mono" ]; then
    show_message "[1/11] Downloading and installing Mono..."
    if [ ! -f "$MONO_MSI" ]; then
        if ! aria2c -x 8 -s 8 -k 1M --dir="$DOWNLOAD_DIR" -o "mono-${MONO_VERSION}.msi" "$mono_url"; then
            show_message "[1/11] ERROR: Failed to download Mono from $mono_url" >&2
            exit 2
        fi
    else
        show_message "[1/11] Mono installer already present and valid in $MONO_MSI. Skipping download."
    fi
    if ! WINEDLLOVERRIDES=mscoree=d $wine_executable msiexec /i "$MONO_MSI" /qn; then
        show_message "[1/11] ERROR: Mono installation failed." >&2
        exit 3
    fi
    show_message "[1/11] Mono installed."
else
    show_message "[1/11] Mono is already installed."
fi

# Gecko download and install
GECKO_MSI="$DOWNLOAD_DIR/wine-gecko-${GECKO_VERSION}.msi"
if ! is_wine_gecko_installed; then
    show_message "[PRE] Downloading and installing Wine Gecko in unattended mode..."
    if [ ! -f "$GECKO_MSI" ]; then
        if ! aria2c -x 8 -s 8 -k 1M --dir="$DOWNLOAD_DIR" -o "wine-gecko-${GECKO_VERSION}.msi" "$gecko_url"; then
            show_message "[PRE] ERROR: Failed to download Wine Gecko from $gecko_url" >&2
            exit 4
        fi
    else
        show_message "[PRE] Wine Gecko installer already present and valid in $GECKO_MSI. Skipping download."
    fi
    if ! $wine_executable msiexec /i "$GECKO_MSI" /qn; then
        show_message "[PRE] ERROR: Wine Gecko installation failed." >&2
        exit 5
    fi
    show_message "[PRE] Wine Gecko installed."
else
    show_message "[PRE] Wine Gecko already installed."
fi

export WINEDLLOVERRIDES="ucrtbase=n,b"
winetricks --force -q vcrun2019 gdiplus
winetricks --force -q win10

# MT5 download and install
MT5_EXE="$DOWNLOAD_DIR/mt5setup-${MT5_VERSION}.exe"
if [ ! -e "$mt5file" ]; then
    show_message "[2/11] File $mt5file is not installed. Installing..."
    $wine_executable reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win10" /f
    show_message "[3/11] Downloading MT5 installer..."
    if [ ! -f "$MT5_EXE" ]; then
        if ! aria2c -x 8 -s 8 -k 1M --dir="$DOWNLOAD_DIR" -o "mt5setup-${MT5_VERSION}.exe" "$mt5setup_url"; then
            show_message "[3/11] ERROR: Failed to download MT5 installer from $mt5setup_url" >&2
            exit 6
        fi
    else
        show_message "[3/11] MT5 installer already present and valid in $MT5_EXE. Skipping download."
    fi
    show_message "[3/11] Installing MetaTrader 5..."
    $wine_executable "$MT5_EXE" "/auto" &
    wait
else
    show_message "[2/11] File $mt5file already exists."
fi

# Git download and install
GIT_EXE="$DOWNLOAD_DIR/git-installer-${GIT_VERSION}.exe"
if ! $wine_executable cmd /c git --version 2>/dev/null; then
    show_message "[3/11] Installing Git for Windows in Wine..."
    if [ ! -f "$GIT_EXE" ]; then
        if ! aria2c -x 8 -s 8 -k 1M --dir="$DOWNLOAD_DIR" -o "git-installer-${GIT_VERSION}.exe" "$git_url"; then
            show_message "[3/11] ERROR: Failed to download Git installer from $git_url" >&2
            exit 7
        fi
    else
        show_message "[3/11] Git installer already present and valid in $GIT_EXE. Skipping download."
    fi
    $wine_executable "$GIT_EXE" /VERYSILENT /NORESTART
    show_message "[3/11] Git for Windows installed in Wine."
else
    show_message "[3/11] Git for Windows is already installed in Wine."
fi

# Recheck if MetaTrader 5 is installed
if [ -e "$mt5file" ]; then
    show_message "[3/11] File $mt5file is installed. Running MT5..."
    $wine_executable "$mt5file" &
else
    show_message "[3/11] File $mt5file is not installed. MT5 cannot be run."
fi

# Python download and install
PYTHON_EXE="$DOWNLOAD_DIR/python-installer-${PYTHON_VERSION}.exe"
if ! $wine_executable python --version 2>/dev/null; then
    show_message "[4/11] Installing Python 3.12.10 64-bit in Wine..."
    if [ ! -f "$PYTHON_EXE" ]; then
        if ! aria2c -x 8 -s 8 -k 1M --dir="$DOWNLOAD_DIR" -o "python-installer-${PYTHON_VERSION}.exe" "$python_url"; then
            show_message "[4/11] ERROR: Failed to download Python installer from $python_url" >&2
            exit 8
        fi
    else
        show_message "[4/11] Python installer already present and valid in $PYTHON_EXE. Skipping download."
    fi
    $wine_executable "$PYTHON_EXE" /quiet InstallAllUsers=1 PrependPath=1 Include_launcher=1 Include_pip=1 Include_dev=1 Include_symbols=1 Include_tcltk=1 Include_test=1 SimpleInstall=0
    show_message "[4/11] Python 3.12.10 64-bit installed in Wine."
else
    show_message "[4/11] Python is already installed in Wine."
fi

# Upgrade pip and install required packages
show_message "[5/11] Installing Python libraries"
if [ -n "$win_pip_opts" ]; then
    $wine_executable python -m pip install --upgrade "$win_pip_opts" pip
else
    $wine_executable python -m pip install --upgrade pip
fi

# Install MetaTrader5 library in Windows if not installed
show_message "[6/11] Installing MetaTrader5 library in Windows"
if ! is_wine_python_package_installed "MetaTrader5==$metatrader_version"; then
    if [ -n "$win_pip_opts" ]; then
        $wine_executable python -m pip install "$win_pip_opts" MetaTrader5==$metatrader_version
    else
        $wine_executable python -m pip install MetaTrader5==$metatrader_version
    fi
fi

# Install mt5linux library in Windows if not installed
show_message "[7/11] Checking and installing mt5linux library in Windows if necessary"
if ! is_wine_python_package_installed "mt5linux"; then
    if [ -n "$win_pip_opts" ]; then
        $wine_executable python -m pip install "$win_pip_opts" $mt5linux_pip
    else
        $wine_executable python -m pip install $mt5linux_pip
    fi
fi

# Install mt5linux library in Linux if not installed
show_message "[8/11] Checking and installing mt5linux library in Linux if necessary"
if ! is_python_package_installed "mt5linux"; then
    pip install --upgrade $lnx_pip_opts $mt5linux_pip
fi

# Install pyxdg library in Linux if not installed
show_message "[9/11] Checking and installing pyxdg library in Linux if necessary"
if ! is_python_package_installed "pyxdg"; then
    pip install --upgrade $lnx_pip_opts pyxdg
fi

# Start the MT5 server on Linux
show_message "[10/11] Starting the mt5linux server..."
python3 -m mt5linux --host 0.0.0.0 -p $mt5server_port -w $wine_executable python.exe &

# Give the server some time to start
sleep 5

# Check if the server is running
if ss -tuln | grep ":$mt5server_port" > /dev/null; then
    show_message "[11/11] The mt5linux server is running on port $mt5server_port."
else
    show_message "[11/11] Failed to start the mt5linux server on port $mt5server_port."
fi

