FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm

# set version label
ARG BUILD_DATE
ARG VERSION
# OCI-compliant image metadata
LABEL org.opencontainers.image.title="MetaTrader5 Docker (fork)"
LABEL org.opencontainers.image.description="Fork of MetaTrader5 Docker image with minor tweaks and attribution."
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.authors="glendekoning"
LABEL org.opencontainers.image.url="https://github.com/glendekoning/mt5-docker"
LABEL org.opencontainers.image.source="https://github.com/glendekoning/mt5-docker"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.ref.name="mt5-docker"
LABEL org.opencontainers.image.vendor="glendekoning"
# Preserve original attribution
LABEL org.opencontainers.image.base.name="ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm"
LABEL org.opencontainers.image.revision="forked from gmag11/MetaTrader5-Docker-Image"
LABEL build_version="Metatrader Docker:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="glendekoning"

ENV TITLE=Metatrader5
ENV WINEPREFIX="/config/.wine"
ENV WINEDEBUG=-all
ENV ENABLE_WIN_DOTNET=1
ENV WINEDLLOVERRIDES="mscoree,mscoreei=n,b"

# Install all packages in a single layer to reduce image size
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl \
    gnupg2 \
    software-properties-common \
    ca-certificates \
    cabextract \
    winetricks \
    && mkdir -pm755 /etc/apt/keyrings \
    && wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key \
    && wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/bookworm/winehq-bookworm.sources \
    && dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y --install-recommends winehq-stable winetricks cabextract \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /etc/apt/keyrings/winehq-archive.key

## Mono/Gecko handling moved to Metatrader/start.sh to avoid duplication

## NOTE: Runtime installation strategy
## Installing .NET and Winetricks components at build-time conflicts with a full `/config` bind mount.
## We now install all Windows dependencies in `Metatrader/start.sh` with an idempotent marker.
## This keeps the image generic and lets the mounted prefix persist everything.


COPY /Metatrader /Metatrader
RUN chmod +x /Metatrader/start.sh
COPY /root /

EXPOSE 3000 8001
VOLUME /config
