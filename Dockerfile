# syntax=docker/dockerfile:1.4
# Enable BuildKit features for cache mounts

# ============================================================
# BASE IMAGE
# ============================================================
FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm AS base

# Version ARGs (centralized for all stages)
ARG BUILD_DATE
ARG VERSION
# Python 3.12: Required for numpy 1.26.4 pre-built wheels (3.13 has no wheels)
ARG PYTHON_VERSION=3.12.8
ARG GECKO_VERSION=2.47.4
ARG RPYC_VERSION=6.0.2
ARG PLUMBUM_VERSION=1.8.0
# NumPy 1.26.4: Wine compatible (2.x uses ucrtbase functions Wine hasn't implemented)
ARG NUMPY_VERSION=1.26.4

# Feature flags - non-free components installed at runtime for MT5
ARG ENABLE_WINETRICKS_NONFREE=0

# ============================================================
# Stage 1: WINE-BASE - Base image with Wine installed (SHARED)
# This layer is used by both wine-builder and runtime
# ============================================================
FROM base AS wine-base

# Install Wine ONCE - shared between builder and runtime
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        xvfb python3 python3-pip python3-venv python3-xdg \
        wget curl gnupg2 ca-certificates cabextract && \
    # Wine repository
    mkdir -pm755 /etc/apt/keyrings && \
    wget -q -O /etc/apt/keyrings/winehq-archive.key \
        "https://dl.winehq.org/wine-builds/winehq.key" && \
    wget -qNP /etc/apt/sources.list.d/ \
        "https://dl.winehq.org/wine-builds/debian/dists/bookworm/winehq-bookworm.sources" && \
    dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --install-recommends winehq-stable winetricks

# ============================================================
# Stage 2: DOWNLOADER - Pre-download large files with caching
# ============================================================
FROM base AS downloader

ARG PYTHON_VERSION
ARG GECKO_VERSION
ARG RPYC_VERSION
ARG PLUMBUM_VERSION
ARG NUMPY_VERSION

WORKDIR /staging

# Download large files with BuildKit cache (MT5 downloaded at runtime for latest version)
RUN --mount=type=cache,target=/downloads,id=mt5-downloads,sharing=locked \
    set -ex && \
    # Python Installer (~30MB)
    if [ ! -f /downloads/python-${PYTHON_VERSION}-amd64.exe ]; then \
        echo "Downloading Python ${PYTHON_VERSION}..." && \
        curl -fSL -o /downloads/python-${PYTHON_VERSION}-amd64.exe \
            "https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe"; \
    fi && \
    cp /downloads/python-${PYTHON_VERSION}-amd64.exe /staging/python-installer.exe && \
    # Gecko x64 (~50MB)
    if [ ! -f /downloads/wine-gecko-${GECKO_VERSION}-x86_64.msi ]; then \
        echo "Downloading Gecko x64..." && \
        curl -fSL -o /downloads/wine-gecko-${GECKO_VERSION}-x86_64.msi \
            "https://dl.winehq.org/wine/wine-gecko/${GECKO_VERSION}/wine-gecko-${GECKO_VERSION}-x86_64.msi"; \
    fi && \
    cp /downloads/wine-gecko-${GECKO_VERSION}-x86_64.msi /staging/ && \
    # Gecko x86 (~30MB)
    if [ ! -f /downloads/wine-gecko-${GECKO_VERSION}-x86.msi ]; then \
        echo "Downloading Gecko x86..." && \
        curl -fSL -o /downloads/wine-gecko-${GECKO_VERSION}-x86.msi \
            "https://dl.winehq.org/wine/wine-gecko/${GECKO_VERSION}/wine-gecko-${GECKO_VERSION}-x86.msi"; \
    fi && \
    cp /downloads/wine-gecko-${GECKO_VERSION}-x86.msi /staging/ && \
    # Create version manifest (MT5 version not pinned - always latest at runtime)
    echo "PYTHON_VERSION=${PYTHON_VERSION}" > /staging/.versions && \
    echo "GECKO_VERSION=${GECKO_VERSION}" >> /staging/.versions && \
    echo "RPYC_VERSION=${RPYC_VERSION}" >> /staging/.versions && \
    echo "PLUMBUM_VERSION=${PLUMBUM_VERSION}" >> /staging/.versions && \
    echo "NUMPY_VERSION=${NUMPY_VERSION}" >> /staging/.versions && \
    echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /staging/.versions && \
    ls -la /staging/

# ============================================================
# Stage 3: WINE-BUILDER - Build Wine prefix with Python + packages
# Uses wine-base (Wine already installed)
# ============================================================
FROM wine-base AS wine-builder

ARG PYTHON_VERSION
ARG GECKO_VERSION
ARG RPYC_VERSION
ARG PLUMBUM_VERSION
ARG NUMPY_VERSION
ARG ENABLE_WINETRICKS_NONFREE

# Build complete Wine prefix (Python + packages, NOT MT5)
# Pattern from webcomics/pywine: xvfb-run + proper DLL overrides
RUN --mount=from=downloader,source=/staging,target=/staging \
    set -eux && \
    umask 0 && \
    export WINEDEBUG=-all && \
    export WINEARCH=win64 && \
    export WINEDLLOVERRIDES="winemenubuilder.exe,mscoree,mshtml=" && \
    export WINEPREFIX=/wine-build && \
    export HOME=/tmp && \
    export WINETRICKS_UNATTENDED=1 && \
    export XDG_CACHE_HOME=/tmp/.cache && \
    export W_CACHE=/tmp/.cache/winetricks && \
    mkdir -p /wine-build /tmp/.cache/winetricks && \
    # ============================================================
    # Step 1: Initialize Wine prefix (pywine pattern)
    # ============================================================
    echo "=== Step 1/5: Initializing Wine prefix ===" && \
    xvfb-run sh -c "\
        wine reg add 'HKCU\\Software\\Wine\\DllOverrides' /v winemenubuilder.exe /t REG_SZ /d '' /f && \
        wine reg add 'HKCU\\Software\\Wine\\DllOverrides' /v mscoree /t REG_SZ /d '' /f && \
        wine reg add 'HKCU\\Software\\Wine\\DllOverrides' /v mshtml /t REG_SZ /d '' /f && \
        wineserver -w" && \
    test -d /wine-build/drive_c || { echo "FAIL: Wine prefix not created"; exit 1; } && \
    # ============================================================
    # Step 2: Install Gecko
    # ============================================================
    echo "=== Step 2/5: Installing Gecko ===" && \
    xvfb-run sh -c "\
        wine msiexec /i /staging/wine-gecko-${GECKO_VERSION}-x86_64.msi /quiet && \
        wine msiexec /i /staging/wine-gecko-${GECKO_VERSION}-x86.msi /quiet && \
        wineserver -w" && \
    # ============================================================
    # Step 3: Install winetricks win10
    # ============================================================
    echo "=== Step 3/5: Installing winetricks win10 ===" && \
    xvfb-run sh -c "winetricks -q win10; wineserver -w" && \
    rm -rf /tmp/.cache/winetricks/* && \
    # Optional: Non-free components
    if [ "${ENABLE_WINETRICKS_NONFREE}" = "1" ]; then \
        echo "Installing non-free winetricks components..." && \
        for pkg in vcrun2019 vcrun2022 corefonts gdiplus; do \
            xvfb-run sh -c "winetricks -q $pkg; wineserver -w" || echo "WARN: $pkg failed"; \
            rm -rf /tmp/.cache/winetricks/*; \
        done; \
    fi && \
    # ============================================================
    # Step 4: Install Python for Windows (pywine pattern)
    # ============================================================
    echo "=== Step 4/5: Installing Python ${PYTHON_VERSION} ===" && \
    xvfb-run sh -c "\
        wine /staging/python-installer.exe /quiet TargetDir=C:\\\\Python Include_doc=0 InstallAllUsers=1 PrependPath=1 Include_pip=1 && \
        wineserver -w" && \
    # Verify Python
    PYTHON_EXE="/wine-build/drive_c/Python/python.exe" && \
    test -f "$PYTHON_EXE" || { \
        echo "FAIL: Python not found at $PYTHON_EXE"; \
        find /wine-build/drive_c -name "python.exe" -type f 2>/dev/null; \
        exit 1; \
    } && \
    echo "Python found at: $PYTHON_EXE" && \
    xvfb-run sh -c "wine '$PYTHON_EXE' --version; wineserver -w" || { echo "FAIL: Python cannot execute"; exit 1; } && \
    # ============================================================
    # Step 5: Install Python packages (NOT MetaTrader5 - runtime only)
    # ============================================================
    echo "=== Step 5/5: Installing Python packages ===" && \
    xvfb-run sh -c "\
        wine '$PYTHON_EXE' -m pip install --upgrade --no-cache-dir pip && \
        wine '$PYTHON_EXE' -m pip install --no-cache-dir \
            'rpyc==${RPYC_VERSION}' \
            'numpy==${NUMPY_VERSION}' \
            'plumbum>=${PLUMBUM_VERSION}' \
            'structlog>=25.5' \
            'python-dateutil' && \
        wine '$PYTHON_EXE' -m pip install --no-cache-dir \
            'https://github.com/marlonsc/mt5linux/archive/refs/heads/master.tar.gz' && \
        wineserver -w" && \
    # Cleanup
    echo "=== Cleanup ===" && \
    rm -rf /tmp/.wine-* /tmp/.cache /tmp/.X* && \
    rm -rf /wine-build/drive_c/users/*/Temp/* 2>/dev/null || true && \
    rm -rf /wine-build/drive_c/windows/temp/* 2>/dev/null || true && \
    touch /wine-build/.build-complete && \
    echo "=== BUILD COMPLETE ===" && \
    du -sh /wine-build

# ============================================================
# Stage 4: RUNTIME - Final image (uses wine-base = Wine pre-installed)
# ============================================================
FROM wine-base AS runtime

# Version ARGs for labels
ARG BUILD_DATE
ARG VERSION
ARG PYTHON_VERSION
ARG GECKO_VERSION
ARG RPYC_VERSION
ARG PLUMBUM_VERSION
ARG NUMPY_VERSION

# OCI-compliant image metadata
LABEL org.opencontainers.image.title="MetaTrader5 Docker (fork)"
LABEL org.opencontainers.image.description="MetaTrader5 with pre-built Wine prefix and mt5linux integration"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.authors="marlonsc"
LABEL org.opencontainers.image.url="https://github.com/marlonsc/mt5-docker"
LABEL org.opencontainers.image.source="https://github.com/marlonsc/mt5-docker"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.ref.name="mt5-docker"
LABEL org.opencontainers.image.vendor="marlonsc"
LABEL org.opencontainers.image.base.name="ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm"
LABEL build_version="Metatrader Docker:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="marlonsc"
LABEL mt5.python.version="${PYTHON_VERSION}"
LABEL mt5.gecko.version="${GECKO_VERSION}"

# Environment variables
ENV TITLE=Metatrader5
ENV WINEPREFIX="/config/.wine"
ENV WINEDEBUG=-all
ENV WINEDLLOVERRIDES="winemenubuilder.exe,mscoree,mshtml="
ENV STAGING_DIR="/opt/mt5-staging"
ENV WINE_PREFIX_TEMPLATE="/opt/wine-prefix-template"

# Linux Python packages (for mt5linux host-side RPyC client)
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    python3 -m pip install --upgrade --break-system-packages pip && \
    python3 -m pip install --break-system-packages \
        "numpy==${NUMPY_VERSION}" \
        "rpyc==${RPYC_VERSION}" \
        "plumbum>=${PLUMBUM_VERSION}" \
        "pyparsing>=3.0.0" \
        pyxdg && \
    python3 -m pip install --break-system-packages --ignore-requires-python \
        "https://github.com/marlonsc/mt5linux/archive/refs/heads/master.tar.gz"

# Copy version manifest (MT5 downloaded at container startup for latest version)
COPY --from=downloader /staging/.versions /opt/mt5-staging/.versions

# Copy pre-built Wine prefix as TEMPLATE (copied to /config/.wine at container startup)
COPY --from=wine-builder /wine-build /opt/wine-prefix-template

# Copy scripts
COPY /Metatrader /Metatrader
RUN chmod +x /Metatrader/start.sh && \
    chmod -R +x /Metatrader/scripts && \
    chown -R abc:abc /Metatrader

# Copy s6 service definitions for RPyC server supervision
COPY /Metatrader/etc/s6-overlay /etc/s6-overlay
RUN chmod +x /etc/s6-overlay/s6-rc.d/svc-mt5server/run && \
    chmod +x /etc/s6-overlay/s6-rc.d/svc-mt5server/finish

# Copy LinuxServer.io defaults
COPY /root /

EXPOSE 3000 8001
VOLUME /config
