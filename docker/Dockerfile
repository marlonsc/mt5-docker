# syntax=docker/dockerfile:1.4
# Enable BuildKit features for cache mounts

# ============================================================
# BASE IMAGE - Debian Bookworm with KasmVNC
# ============================================================
FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm AS base

# Version ARGs (centralized for all stages)
ARG BUILD_DATE
ARG VERSION
# Python 3.12: Required for numpy 1.26.4 pre-built wheels (Wine side)
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
    # Wine 10.0 with full i386 support (required for wine64 loader to work).
    # Pin ALL wine-stable sub-packages, not just the winehq-stable meta: since
    # WineHQ shipped 11.0.0.0 stable, a meta-only pin lets apt drift the amd64
    # sub-package to 11.0 ("but 11.0.0.0~bookworm-1 is to be installed") and the
    # version set becomes unsatisfiable. Pinning all four keeps 10.0 (which the
    # MT5 anti-debug check requires) resolvable.
    apt-get install -y --install-recommends \
        winehq-stable=10.0.0.0~bookworm-1 \
        wine-stable=10.0.0.0~bookworm-1 \
        wine-stable-amd64=10.0.0.0~bookworm-1 \
        wine-stable-i386=10.0.0.0~bookworm-1

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
# MetaTrader5 connector pin; baked into the .versions manifest for runtime setup.sh
ARG MT5_PYPI_VERSION=5.0.5735

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
    echo "MT5_PYPI_VERSION=${MT5_PYPI_VERSION}" >> /staging/.versions && \
    echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /staging/.versions && \
    echo "BASE_IMAGE=debianbookworm" >> /staging/.versions && \
    ls -la /staging/

# ============================================================
# Stage 3: RUNTIME - Final image
# ============================================================
# NOTE: The Wine prefix (Mono + Gecko + Python + gRPC packages) is built at
# RUNTIME on first boot by setup.sh:init_wine_prefix, NOT at image-build time.
# A former `wine-builder` BuildKit stage did this at build time, but the Wine
# prefix build (Xvfb + wineserver + msiexec) is timing-sensitive and raced
# against BuildKit's concurrent stage scheduling (the runtime apt layer ran
# interleaved with it), causing nondeterministic Gecko msiexec failures
# (exit 91 / "X connection broken"). The identical steps succeed every time in
# a single isolated container (`docker run`), which is exactly what first-boot
# is. Building at runtime also persists the prefix to the /config volume
# (idempotent across restarts) and keeps the image build cheap and deterministic.
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
ENV WINEDLLOVERRIDES="winemenubuilder.exe,mscoree="
ENV STAGING_DIR="/opt/mt5-staging"

# GUI automation deps (Debian main) for headless demo-account creation.
# Installed in the runtime layer (not wine-base) so the heavy cached Wine layer
# is reused on rebuild and we never re-resolve the pinned winehq packages.
# x11-utils provides xdpyinfo (Xvfb readiness poll in init_wine_prefix).
# xclip reads the X clipboard so the wizard can capture the demo account's
# MetaQuotes-generated password (copied from the final wizard page) EXACTLY --
# no OCR misreads -- and persist it to startup.ini for restart-survival.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        xdotool \
        wmctrl \
        xclip \
        x11-utils && \
    rm -rf /var/lib/apt/lists/*

# Copy version manifest + Wine prefix installer payload (Python/Mono/Gecko msi).
# setup.sh:init_wine_prefix consumes these at first boot to build the prefix.
COPY --from=downloader /staging /opt/mt5-staging

# Copy scripts
COPY container/metatrader /Metatrader
RUN chmod +x /Metatrader/start.sh && \
    chmod +x /Metatrader/setup.sh && \
    chmod +x /Metatrader/health_monitor.sh && \
    chown -R abc:abc /Metatrader

# Copy s6 service definitions
COPY container/metatrader/etc/s6-overlay /etc/s6-overlay
RUN chmod +x /etc/s6-overlay/s6-rc.d/svc-mt5server/run && \
    chmod +x /etc/s6-overlay/s6-rc.d/svc-mt5server/finish

# Copy LinuxServer.io defaults
COPY container/root /

EXPOSE 3000 8001
VOLUME /config
