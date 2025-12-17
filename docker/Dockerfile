# syntax=docker/dockerfile:1.4
# Enable BuildKit features for cache mounts

# ============================================================
# BASE IMAGE - Alpine 3.21 with KasmVNC
# ============================================================
FROM ghcr.io/linuxserver/baseimage-kasmvnc:alpine321 AS base

# Version ARGs (centralized for all stages)
ARG BUILD_DATE
ARG VERSION
# Python 3.12: Required for numpy 1.26.4 pre-built wheels
ARG PYTHON_VERSION=3.12
# gRPC 1.76.0: Required by mt5_pb2_grpc.py (GRPC_GENERATED_VERSION)
ARG GRPCIO_VERSION=1.76.0
# NumPy 1.26.4: Wine compatible (2.x uses ucrtbase functions Wine hasn't implemented)
ARG NUMPY_VERSION=1.26.4
# Wine Mono 9.4.0: Compatible with Wine 9.17 (Alpine 3.21)
ARG WINE_MONO_VERSION=9.4.0

# ============================================================
# Stage 1: WINE-BASE - Base image with Wine installed (SHARED)
# ============================================================
FROM base AS wine-base

# Install Wine and dependencies from Alpine repos
# Wine 9.17 is available in Alpine 3.21 community repo
# NO winetricks - we use direct Wine commands (like original repo)
RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk update && \
    apk add --no-cache \
        # Wine (no gecko - we use Mono instead)
        wine \
        # X11 and display
        xvfb-run \
        # Python (Linux side)
        python3 \
        py3-pip \
        # Build tools and utilities
        wget \
        curl \
        ca-certificates \
        bash \
        coreutils \
        # Free fonts (required for MT5 UI)
        font-liberation \
        font-dejavu \
        font-noto \
        fontconfig \
        # gcompat for glibc compatibility if needed
        gcompat

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

RUN apk add --no-cache curl

WORKDIR /staging

# Download large files with BuildKit cache
RUN --mount=type=cache,target=/downloads,id=mt5-downloads-alpine,sharing=locked \
    set -ex && \
    # Python Installer for Windows (~30MB)
    PYTHON_FULL_VERSION="3.12.8" && \
    if [ ! -f /downloads/python-${PYTHON_FULL_VERSION}-amd64.exe ]; then \
        echo "Downloading Python ${PYTHON_FULL_VERSION}..." && \
        curl -fSL -o /downloads/python-${PYTHON_FULL_VERSION}-amd64.exe \
            "https://www.python.org/ftp/python/${PYTHON_FULL_VERSION}/python-${PYTHON_FULL_VERSION}-amd64.exe"; \
    fi && \
    cp /downloads/python-${PYTHON_FULL_VERSION}-amd64.exe /staging/python-installer.exe && \
    # Wine Mono (~75MB) - for .NET support (like original repo)
    if [ ! -f /downloads/wine-mono-${WINE_MONO_VERSION}-x86.msi ]; then \
        echo "Downloading Wine Mono ${WINE_MONO_VERSION}..." && \
        curl -fSL -o /downloads/wine-mono-${WINE_MONO_VERSION}-x86.msi \
            "https://dl.winehq.org/wine/wine-mono/${WINE_MONO_VERSION}/wine-mono-${WINE_MONO_VERSION}-x86.msi"; \
    fi && \
    cp /downloads/wine-mono-${WINE_MONO_VERSION}-x86.msi /staging/ && \
    # Create version manifest
    echo "PYTHON_VERSION=${PYTHON_FULL_VERSION}" > /staging/.versions && \
    echo "WINE_MONO_VERSION=${WINE_MONO_VERSION}" >> /staging/.versions && \
    echo "GRPCIO_VERSION=${GRPCIO_VERSION}" >> /staging/.versions && \
    echo "NUMPY_VERSION=${NUMPY_VERSION}" >> /staging/.versions && \
    echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /staging/.versions && \
    echo "BASE_IMAGE=alpine321" >> /staging/.versions && \
    ls -la /staging/

# ============================================================
# Stage 3: WINE-BUILDER - Build Wine prefix with Python + packages
# ============================================================
FROM wine-base AS wine-builder

ARG PYTHON_VERSION
ARG GRPCIO_VERSION
ARG NUMPY_VERSION
ARG WINE_MONO_VERSION

# Build complete Wine prefix (Python + packages, NOT MT5)
# Following original repo approach: Mono + direct registry (no winetricks)
RUN --mount=from=downloader,source=/staging,target=/staging \
    set -eux && \
    umask 0 && \
    export WINEDEBUG=-all && \
    export WINEARCH=win64 && \
    export WINEPREFIX=/wine-build && \
    export HOME=/tmp && \
    mkdir -p /wine-build && \
    # ============================================================
    # Step 1: Initialize Wine prefix with DLL overrides
    # ============================================================
    echo "=== Step 1/5: Initializing Wine prefix ===" && \
    xvfb-run -a sh -c "\
        wine reg add 'HKCU\\Software\\Wine\\DllOverrides' /v winemenubuilder.exe /t REG_SZ /d '' /f && \
        wine reg add 'HKCU\\Software\\Wine\\DllOverrides' /v mscoree /t REG_SZ /d '' /f && \
        wine reg add 'HKCU\\Software\\Wine\\DllOverrides' /v mshtml /t REG_SZ /d '' /f && \
        wineserver -w" && \
    test -d /wine-build/drive_c || { echo "FAIL: Wine prefix not created"; exit 1; } && \
    # ============================================================
    # Step 2: Install Wine Mono (for .NET support, like original repo)
    # ============================================================
    echo "=== Step 2/5: Installing Wine Mono ${WINE_MONO_VERSION} ===" && \
    export WINEDLLOVERRIDES="mscoree=d" && \
    xvfb-run -a sh -c "\
        wine msiexec /i /staging/wine-mono-${WINE_MONO_VERSION}-x86.msi /quiet && \
        wineserver -w" && \
    unset WINEDLLOVERRIDES && \
    # ============================================================
    # Step 3: Set Windows version to win10 (via registry, no winetricks)
    # ============================================================
    echo "=== Step 3/5: Setting Windows version to win10 ===" && \
    xvfb-run -a sh -c "\
        wine reg add 'HKEY_CURRENT_USER\\Software\\Wine' /v Version /t REG_SZ /d 'win10' /f && \
        wineserver -w" && \
    # ============================================================
    # Step 4: Install Python for Windows
    # ============================================================
    echo "=== Step 4/5: Installing Python ===" && \
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
    # Step 5: Install Python packages (grpcio + numpy + protobuf)
    # ============================================================
    echo "=== Step 5/5: Installing Python packages (grpcio + numpy + protobuf) ===" && \
    xvfb-run -a sh -c "\
        wine '$PYTHON_EXE' -m pip install --upgrade --no-cache-dir pip && \
        wine '$PYTHON_EXE' -m pip install --no-cache-dir \
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

# OCI-compliant image metadata
LABEL org.opencontainers.image.title="MetaTrader5 Docker Alpine"
LABEL org.opencontainers.image.description="MetaTrader5 with Wine on Alpine 3.21"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.authors="marlonsc"
LABEL org.opencontainers.image.url="https://github.com/marlonsc/mt5-docker"
LABEL org.opencontainers.image.source="https://github.com/marlonsc/mt5-docker"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.ref.name="mt5-docker-alpine"
LABEL org.opencontainers.image.vendor="marlonsc"
LABEL org.opencontainers.image.base.name="ghcr.io/linuxserver/baseimage-kasmvnc:alpine321"
LABEL build_version="Metatrader Docker Alpine:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="marlonsc"
LABEL mt5.python.version="${PYTHON_VERSION}"
LABEL mt5.grpcio.version="${GRPCIO_VERSION}"
LABEL mt5.wine.mono.version="${WINE_MONO_VERSION}"
LABEL mt5.base.os="alpine321"

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
