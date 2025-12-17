# syntax=docker/dockerfile:1.4
# Enable BuildKit features for cache mounts

# ============================================================
# BASE IMAGE - Debian Bookworm with KasmVNC
# ============================================================
FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm AS base

# Version ARGs (centralized for all stages)
ARG BUILD_DATE
ARG VERSION
# Python 3.12: Required for numpy 1.26.4 pre-built wheels
ARG PYTHON_VERSION=3.12
# gRPC 1.76.0: Required by mt5_pb2_grpc.py (GRPC_GENERATED_VERSION)
ARG GRPCIO_VERSION=1.76.0
# NumPy 1.26.4: Wine 10.0 compatible (2.x requires crealf() not in Wine 10.0)
ARG NUMPY_VERSION=1.26.4
# Wine Mono 10.4.0: Compatible with Wine 10.x
ARG WINE_MONO_VERSION=10.4.0
# Wine Gecko 2.47.4: HTML rendering support for Wine 10.x
ARG WINE_GECKO_VERSION=2.47.4

# ============================================================
# Stage 1: WINE-BASE - Base image with Wine 10.0 installed
# ============================================================
FROM base AS wine-base

# Layer 1: Base packages (rarely changes)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        # X11 and display
        xvfb \
        # Python (Linux side)
        python3 \
        python3-pip \
        python3-venv \
        # Build tools and utilities
        wget \
        curl \
        gnupg2 \
        ca-certificates \
        software-properties-common \
        cabextract \
        # Fonts (required for MT5 UI)
        fonts-liberation \
        fonts-dejavu \
        fontconfig && \
    mkdir -pm755 /etc/apt/keyrings && \
    wget -q -O /etc/apt/keyrings/winehq-archive.key \
        "https://dl.winehq.org/wine-builds/winehq.key" && \
    wget -qNP /etc/apt/sources.list.d/ \
        "https://dl.winehq.org/wine-builds/debian/dists/bookworm/winehq-bookworm.sources" && \
    dpkg --add-architecture i386 && \
    apt-get update && \
    # Wine 10.0 with full i386 support (required for wine64 loader to work)
    apt-get install -y --install-recommends \
        winehq-stable=10.0.0.0~bookworm-1

# Update font cache
RUN fc-cache -fv

# ============================================================
# Stage 2: DOWNLOADER - Pre-download large files with caching
# ============================================================
FROM base AS downloader

ARG PYTHON_VERSION
ARG GRPCIO_VERSION
ARG NUMPY_VERSION
ARG WINE_MONO_VERSION
ARG WINE_GECKO_VERSION

WORKDIR /staging

# Download large files with BuildKit cache
RUN --mount=type=cache,target=/downloads,id=mt5-downloads-debian,sharing=locked \
    set -ex && \
    # Python Installer for Windows (~30MB)
    PYTHON_FULL_VERSION="3.12.8" && \
    if [ ! -f /downloads/python-${PYTHON_FULL_VERSION}-amd64.exe ]; then \
        echo "Downloading Python ${PYTHON_FULL_VERSION}..." && \
        curl -fSL -o /downloads/python-${PYTHON_FULL_VERSION}-amd64.exe \
            "https://www.python.org/ftp/python/${PYTHON_FULL_VERSION}/python-${PYTHON_FULL_VERSION}-amd64.exe"; \
    fi && \
    cp /downloads/python-${PYTHON_FULL_VERSION}-amd64.exe /staging/python-installer.exe && \
    # Wine Mono (~75MB) - for .NET support
    if [ ! -f /downloads/wine-mono-${WINE_MONO_VERSION}-x86.msi ]; then \
        echo "Downloading Wine Mono ${WINE_MONO_VERSION}..." && \
        curl -fSL -o /downloads/wine-mono-${WINE_MONO_VERSION}-x86.msi \
            "https://dl.winehq.org/wine/wine-mono/${WINE_MONO_VERSION}/wine-mono-${WINE_MONO_VERSION}-x86.msi"; \
    fi && \
    cp /downloads/wine-mono-${WINE_MONO_VERSION}-x86.msi /staging/ && \
    # Wine Gecko x86_64 (~52MB) - for HTML rendering support
    if [ ! -f /downloads/wine-gecko-${WINE_GECKO_VERSION}-x86_64.msi ]; then \
        echo "Downloading Wine Gecko x86_64 ${WINE_GECKO_VERSION}..." && \
        curl -fSL -o /downloads/wine-gecko-${WINE_GECKO_VERSION}-x86_64.msi \
            "https://dl.winehq.org/wine/wine-gecko/${WINE_GECKO_VERSION}/wine-gecko-${WINE_GECKO_VERSION}-x86_64.msi"; \
    fi && \
    cp /downloads/wine-gecko-${WINE_GECKO_VERSION}-x86_64.msi /staging/ && \
    # Wine Gecko x86 (~30MB) - for 32-bit support
    if [ ! -f /downloads/wine-gecko-${WINE_GECKO_VERSION}-x86.msi ]; then \
        echo "Downloading Wine Gecko x86 ${WINE_GECKO_VERSION}..." && \
        curl -fSL -o /downloads/wine-gecko-${WINE_GECKO_VERSION}-x86.msi \
            "https://dl.winehq.org/wine/wine-gecko/${WINE_GECKO_VERSION}/wine-gecko-${WINE_GECKO_VERSION}-x86.msi"; \
    fi && \
    cp /downloads/wine-gecko-${WINE_GECKO_VERSION}-x86.msi /staging/ && \
    # Create version manifest
    echo "PYTHON_VERSION=${PYTHON_FULL_VERSION}" > /staging/.versions && \
    echo "WINE_MONO_VERSION=${WINE_MONO_VERSION}" >> /staging/.versions && \
    echo "WINE_GECKO_VERSION=${WINE_GECKO_VERSION}" >> /staging/.versions && \
    echo "GRPCIO_VERSION=${GRPCIO_VERSION}" >> /staging/.versions && \
    echo "NUMPY_VERSION=${NUMPY_VERSION}" >> /staging/.versions && \
    echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /staging/.versions && \
    echo "BASE_IMAGE=debianbookworm" >> /staging/.versions && \
    ls -la /staging/

# ============================================================
# Stage 3: WINE-BUILDER - Build Wine prefix with Python + packages
# ============================================================
FROM wine-base AS wine-builder

ARG PYTHON_VERSION
ARG GRPCIO_VERSION
ARG NUMPY_VERSION
ARG WINE_MONO_VERSION
ARG WINE_GECKO_VERSION

# Build complete Wine prefix (Python + packages, NOT MT5)
RUN --mount=from=downloader,source=/staging,target=/staging \
    set -eux && \
    umask 0 && \
    export WINEDEBUG=-all && \
    export WINEARCH=win64 && \
    export WINEPREFIX=/wine-build && \
    export HOME=/tmp && \
    export WINEDLLOVERRIDES="winemenubuilder.exe=d;mscoree=d;mshtml=d" && \
    mkdir -p /wine-build && \
    # ============================================================
    # Step 1: Initialize Wine prefix with DLL overrides
    # ============================================================
    echo "=== Step 1/6: Initializing Wine prefix ===" && \
    xvfb-run -a sh -c "\
        wine reg add 'HKCU\\Software\\Wine\\DllOverrides' /v winemenubuilder.exe /t REG_SZ /d '' /f && \
        wine reg add 'HKCU\\Software\\Wine\\DllOverrides' /v mscoree /t REG_SZ /d '' /f && \
        wine reg add 'HKCU\\Software\\Wine\\DllOverrides' /v mshtml /t REG_SZ /d '' /f && \
        wineserver -w" && \
    test -d /wine-build/drive_c || { echo "FAIL: Wine prefix not created"; exit 1; } && \
    # ============================================================
    # Step 2: Install Wine Mono (for .NET support)
    # ============================================================
    echo "=== Step 2/6: Installing Wine Mono ${WINE_MONO_VERSION} ===" && \
    xvfb-run -a sh -c "\
        wine msiexec /i /staging/wine-mono-${WINE_MONO_VERSION}-x86.msi /quiet && \
        wineserver -w" && \
    # ============================================================
    # Step 3: Install Wine Gecko (for HTML rendering support)
    # ============================================================
    echo "=== Step 3/6: Installing Wine Gecko ${WINE_GECKO_VERSION} ===" && \
    xvfb-run -a sh -c "\
        wine msiexec /i /staging/wine-gecko-${WINE_GECKO_VERSION}-x86_64.msi /quiet && \
        wine msiexec /i /staging/wine-gecko-${WINE_GECKO_VERSION}-x86.msi /quiet && \
        wineserver -w" && \
    # ============================================================
    # Step 4: Set Windows version to win10 (via registry)
    # ============================================================
    echo "=== Step 4/6: Setting Windows version to win10 ===" && \
    xvfb-run -a sh -c "\
        wine reg add 'HKEY_CURRENT_USER\\Software\\Wine' /v Version /t REG_SZ /d 'win10' /f && \
        wineserver -w" && \
    # ============================================================
    # Step 5: Install Python for Windows
    # ============================================================
    echo "=== Step 5/6: Installing Python ===" && \
    xvfb-run -a sh -c "\
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
    xvfb-run -a sh -c "wine '$PYTHON_EXE' --version; wineserver -w" || { echo "FAIL: Python cannot execute"; exit 1; } && \
    # ============================================================
    # Step 6: Install Python packages (grpcio + numpy + protobuf)
    # Use --only-binary to avoid compilation (use prebuilt wheels)
    # ============================================================
    echo "=== Step 6/6: Installing Python packages (grpcio + numpy + protobuf) ===" && \
    xvfb-run -a sh -c "\
        wine '$PYTHON_EXE' -m pip install --upgrade --no-cache-dir pip && \
        wine '$PYTHON_EXE' -m pip install --no-cache-dir --only-binary :all: \
            'grpcio>=${GRPCIO_VERSION}' \
            'protobuf>=4.21.0' \
            'numpy==${NUMPY_VERSION}' && \
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
# Stage 4: RUNTIME - Final image
# ============================================================
FROM wine-base AS runtime

# Version ARGs for labels
ARG BUILD_DATE
ARG VERSION
ARG PYTHON_VERSION
ARG GRPCIO_VERSION
ARG NUMPY_VERSION
ARG WINE_MONO_VERSION
ARG WINE_GECKO_VERSION

# OCI-compliant image metadata
LABEL org.opencontainers.image.title="MetaTrader5 Docker Debian"
LABEL org.opencontainers.image.description="MetaTrader5 with Wine 10.0 on Debian Bookworm"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.authors="marlonsc"
LABEL org.opencontainers.image.url="https://github.com/marlonsc/mt5-docker"
LABEL org.opencontainers.image.source="https://github.com/marlonsc/mt5-docker"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.ref.name="mt5-docker-debian"
LABEL org.opencontainers.image.vendor="marlonsc"
LABEL org.opencontainers.image.base.name="ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm"
LABEL build_version="Metatrader Docker Debian:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="marlonsc"
LABEL mt5.python.version="${PYTHON_VERSION}"
LABEL mt5.grpcio.version="${GRPCIO_VERSION}"
LABEL mt5.wine.mono.version="${WINE_MONO_VERSION}"
LABEL mt5.wine.gecko.version="${WINE_GECKO_VERSION}"
LABEL mt5.base.os="debianbookworm"
LABEL mt5.wine.version="10.0"

# Environment variables
ENV TITLE=Metatrader5
ENV WINEPREFIX="/config/.wine"
ENV WINEDEBUG=-all
ENV WINEDLLOVERRIDES="winemenubuilder.exe,mscoree,mshtml="
ENV STAGING_DIR="/opt/mt5-staging"
ENV WINE_PREFIX_TEMPLATE="/opt/wine-prefix-template"

# Copy version manifest
COPY --from=downloader /staging/.versions /opt/mt5-staging/.versions

# Copy pre-built Wine prefix as TEMPLATE
COPY --from=wine-builder /wine-build /opt/wine-prefix-template

# Copy scripts
COPY container/Metatrader /Metatrader
RUN chmod +x /Metatrader/start.sh && \
    chmod +x /Metatrader/setup.sh && \
    chmod +x /Metatrader/health_monitor.sh && \
    chown -R abc:abc /Metatrader

# Copy s6 service definitions
COPY container/Metatrader/etc/s6-overlay /etc/s6-overlay
RUN chmod +x /etc/s6-overlay/s6-rc.d/svc-mt5server/run && \
    chmod +x /etc/s6-overlay/s6-rc.d/svc-mt5server/finish

# Copy LinuxServer.io defaults
COPY container/root /

EXPOSE 3000 8001
VOLUME /config
