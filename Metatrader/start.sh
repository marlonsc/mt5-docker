#!/bin/bash

# Configuration variables
mt5file='/config/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe'
export WINEPREFIX='/config/.wine'
wine_executable="wine"
metatrader_version="5.0.37"
mt5server_port="8001"
mono_url="https://dl.winehq.org/wine/wine-mono/8.0.0/wine-mono-8.0.0-x86.msi"
python_url="https://www.python.org/ftp/python/3.9.0/python-3.9.0.exe"
mt5setup_url="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
git_url="https://github.com/git-for-windows/git/releases/download/v2.45.1.windows.1/Git-2.45.1-64-bit.exe"
mt5linux_pip="mt5linux@git+https://github.com/marlonsc/mt5linux.git@master"
lnx_pip_opts="--break-system-packages"
win_pip_opts=""

mkdir -p /config/.wine/drive_c/

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

# Check for necessary dependencies
check_dependency "curl"
check_dependency "$wine_executable"

# Install Mono if not present
if [ ! -e "/config/.wine/drive_c/windows/mono" ]; then
    show_message "[1/7] Downloading and installing Mono..."
    curl -o /config/.wine/drive_c/mono.msi $mono_url
    WINEDLLOVERRIDES=mscoree=d $wine_executable msiexec /i /config/.wine/drive_c/mono.msi /qn
    rm /config/.wine/drive_c/mono.msi
    show_message "[1/7] Mono installed."
else
    show_message "[1/7] Mono is already installed."
fi

# Check if MetaTrader 5 is already installed
if [ -e "$mt5file" ]; then
    show_message "[2/7] File $mt5file already exists."
else
    show_message "[2/7] File $mt5file is not installed. Installing..."

    # Set Windows 10 mode in Wine and download and install MT5
    $wine_executable reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win10" /f
    show_message "[3/7] Downloading MT5 installer..."
    curl -o /config/.wine/drive_c/mt5setup.exe $mt5setup_url
    show_message "[3/7] Installing MetaTrader 5..."
    $wine_executable "/config/.wine/drive_c/mt5setup.exe" "/auto" &
    wait
    rm -f /config/.wine/drive_c/mt5setup.exe
fi

# Install Git at Wine if necessary
if ! $wine_executable cmd /c git --version 2>/dev/null; then
    show_message "[4/7] Installing Git for Windows in Wine..."
    curl -L -o /tmp/git-installer.exe $git_url
    $wine_executable /tmp/git-installer.exe /VERYSILENT /NORESTART
    rm /tmp/git-installer.exe
    show_message "[4/7] Git for Windows installed in Wine."
else
    show_message "[4/7] Git for Windows is already installed in Wine."
fi

# Recheck if MetaTrader 5 is installed
if [ -e "$mt5file" ]; then
    show_message "[4/7] File $mt5file is installed. Running MT5..."
    $wine_executable "$mt5file" &
else
    show_message "[4/7] File $mt5file is not installed. MT5 cannot be run."
fi


# Install Python in Wine if not present
if ! $wine_executable python --version 2>/dev/null; then
    show_message "[5/7] Installing Python in Wine..."
    curl -L $python_url -o /tmp/python-installer.exe
    $wine_executable /tmp/python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    rm /tmp/python-installer.exe
    show_message "[5/7] Python installed in Wine."
else
    show_message "[5/7] Python is already installed in Wine."
fi

# Upgrade pip and install required packages
show_message "[6/8] Installing Python libraries"
if [ -n "$win_pip_opts" ]; then
    $wine_executable python -m pip install --upgrade "$win_pip_opts" pip
else
    $wine_executable python -m pip install --upgrade pip
fi

# Install MetaTrader5 library in Windows if not installed
show_message "[7/8] Installing MetaTrader5 library in Windows"
if ! is_wine_python_package_installed "MetaTrader5==$metatrader_version"; then
    if [ -n "$win_pip_opts" ]; then
        $wine_executable python -m pip install "$win_pip_opts" MetaTrader5==$metatrader_version
    else
        $wine_executable python -m pip install MetaTrader5==$metatrader_version
    fi
fi

# Install mt5linux library in Windows if not installed
show_message "[8/8] Checking and installing mt5linux library in Windows if necessary"
if ! is_wine_python_package_installed "mt5linux"; then
    if [ -n "$win_pip_opts" ]; then
        $wine_executable python -m pip install "$win_pip_opts" $mt5linux_pip
    else
        $wine_executable python -m pip install $mt5linux_pip
    fi
fi

# Install mt5linux library in Linux if not installed
show_message "[8/8] Checking and installing mt5linux library in Linux if necessary"
if ! is_python_package_installed "mt5linux"; then
    pip install --upgrade $lnx_pip_opts $mt5linux_pip
fi

# Install pyxdg library in Linux if not installed
show_message "[8/8] Checking and installing pyxdg library in Linux if necessary"
if ! is_python_package_installed "pyxdg"; then
    pip install --upgrade $lnx_pip_opts pyxdg
fi

# Start the MT5 server on Linux
show_message "[8/8] Starting the mt5linux server..."
python3 -m mt5linux --host 0.0.0.0 -p $mt5server_port -w $wine_executable python.exe &

# Give the server some time to start
sleep 5

# Check if the server is running
if ss -tuln | grep ":$mt5server_port" > /dev/null; then
    show_message "[8/8] The mt5linux server is running on port $mt5server_port."
else
    show_message "[8/8] Failed to start the mt5linux server on port $mt5server_port."
fi
