# syntax=docker/dockerfile:1.4
# Enable BuildKit features for cache mounts

# ============================================================
# BASE IMAGE
# ============================================================
FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm AS base

# Version ARGs for cache invalidation and pinning
ARG BUILD_DATE
ARG VERSION
ARG PYTHON_VERSION=3.13.11
ARG GECKO_VERSION=2.47.4
ARG MT5_PYPI_VERSION=5.0.5430

# CENTRALIZED PYTHON MODULE VERSIONS (must match 00_env.sh)
ARG RPYC_VERSION=6.0.2
ARG PYDANTIC_MIN_VERSION=2.0.0
ARG PYDANTIC_MAX_VERSION=3.0.0
ARG PLUMBUM_MIN_VERSION=1.8.0
ARG NUMPY_MAX_VERSION=2

# ============================================================
# Stage 1: DOWNLOADER - Pre-download large files
# ============================================================
FROM base AS downloader

ARG PYTHON_VERSION
ARG GECKO_VERSION
ARG MT5_PYPI_VERSION
ARG RPYC_VERSION
ARG PYDANTIC_MIN_VERSION
ARG PLUMBUM_MIN_VERSION

WORKDIR /staging

# Download all large files with BuildKit cache
# Files cached in /downloads AND copied to /staging for embedding
RUN --mount=type=cache,target=/downloads,id=mt5-downloads,sharing=locked \
    set -ex && \
    # MT5 Setup (~300MB)
    if [ ! -f /downloads/mt5setup.exe ]; then \
        echo "Downloading MT5 setup..." && \
        curl -fSL -o /downloads/mt5setup.exe \
            "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"; \
    fi && \
    cp /downloads/mt5setup.exe /staging/ && \
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
    # Create version manifest for runtime (centralized versions)
    echo "PYTHON_VERSION=${PYTHON_VERSION}" > /staging/.versions && \
    echo "GECKO_VERSION=${GECKO_VERSION}" >> /staging/.versions && \
    echo "MT5_PYPI_VERSION=${MT5_PYPI_VERSION}" >> /staging/.versions && \
    echo "RPYC_VERSION=${RPYC_VERSION}" >> /staging/.versions && \
    echo "PYDANTIC_VERSION=${PYDANTIC_MIN_VERSION}" >> /staging/.versions && \
    echo "PLUMBUM_VERSION=${PLUMBUM_MIN_VERSION}" >> /staging/.versions && \
    echo "NUMPY_VERSION=1.26" >> /staging/.versions && \
    echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /staging/.versions && \
    ls -la /staging/

# ============================================================
# Stage 2: BUILDER - System packages with optimal caching
# ============================================================
FROM base AS builder

# Layer 1: Base packages (rarely changes)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv python3-xdg \
        wget curl gnupg2 software-properties-common \
        ca-certificates cabextract git unzip rsync

# Layer 2: Wine repository setup (rarely changes)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    mkdir -pm755 /etc/apt/keyrings && \
    wget -q -O /etc/apt/keyrings/winehq-archive.key \
        "https://dl.winehq.org/wine-builds/winehq.key" && \
    wget -qNP /etc/apt/sources.list.d/ \
        "https://dl.winehq.org/wine-builds/debian/dists/bookworm/winehq-bookworm.sources" && \
    dpkg --add-architecture i386

# Layer 3: Wine installation (rarely changes, largest layer ~2GB)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && \
    apt-get install -y --install-recommends \
        winehq-stable winetricks cabextract

# Layer 4: Linux Python packages (uses centralized versions from ARGs)
ARG MT5_PYPI_VERSION
ARG RPYC_VERSION
ARG PYDANTIC_MIN_VERSION
ARG PLUMBUM_MIN_VERSION
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    python3 -m pip install --upgrade --break-system-packages pip && \
    python3 -m pip install --break-system-packages \
        "numpy>=2.1.0" "rpyc==${RPYC_VERSION}" "plumbum>=${PLUMBUM_MIN_VERSION}" \
        "pyparsing>=3.0.0" "pydantic>=${PYDANTIC_MIN_VERSION},<3.0" \
        "pydantic-settings>=2.0,<3.0" pyxdg && \
    python3 -m pip install --break-system-packages --ignore-requires-python \
        "git+https://github.com/marlonsc/mt5linux.git@master"

# ============================================================
# Stage 3: RUNTIME - Final image
# ============================================================
FROM builder AS runtime

# Version ARGs for labels
ARG BUILD_DATE
ARG VERSION
ARG PYTHON_VERSION
ARG GECKO_VERSION
ARG MT5_PYPI_VERSION

# OCI-compliant image metadata
LABEL org.opencontainers.image.title="MetaTrader5 Docker (fork)"
LABEL org.opencontainers.image.description="Fork of MetaTrader5 Docker image with optimized build caching"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.authors="glendekoning"
LABEL org.opencontainers.image.url="https://github.com/glendekoning/mt5-docker"
LABEL org.opencontainers.image.source="https://github.com/glendekoning/mt5-docker"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.ref.name="mt5-docker"
LABEL org.opencontainers.image.vendor="glendekoning"
LABEL org.opencontainers.image.base.name="ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm"
LABEL org.opencontainers.image.revision="forked from gmag11/MetaTrader5-Docker-Image"
LABEL build_version="Metatrader Docker:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="glendekoning"
LABEL mt5.python.version="${PYTHON_VERSION}"
LABEL mt5.gecko.version="${GECKO_VERSION}"
LABEL mt5.pypi.version="${MT5_PYPI_VERSION}"

# Environment variables
ENV TITLE=Metatrader5
ENV WINEPREFIX="/config/.wine"
ENV WINEDEBUG=-all
ENV ENABLE_WIN_DOTNET=1
ENV WINEDLLOVERRIDES="mscoree=n,mscorlib=n"
ENV STAGING_DIR="/opt/mt5-staging"
ENV CACHE_DIR="/cache"

# Copy pre-downloaded files to staging location (embedded in image)
COPY --from=downloader /staging /opt/mt5-staging

# Copy scripts (last for best cache reuse on code changes)
COPY /Metatrader /Metatrader
RUN chmod +x /Metatrader/start.sh && chmod -R +x /Metatrader/scripts

# Copy s6 service definitions for RPyC server supervision
COPY /Metatrader/etc/s6-overlay /etc/s6-overlay
RUN chmod +x /etc/s6-overlay/s6-rc.d/svc-mt5server/run && \
    chmod +x /etc/s6-overlay/s6-rc.d/svc-mt5server/finish

COPY /root /

EXPOSE 3000 8001
VOLUME /config /cache
