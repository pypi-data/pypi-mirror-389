# syntax=docker/dockerfile:1
#
# BridgeIt integration test image.
# - Debian 12 (bookworm) base with Python 3.12
# - Provides Jupyter tooling so notebooks can run
# - Leaves all language/runtime installation to bridgeit's `install_lang`

FROM python:3.12-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# Keep the base image lean; only add essentials needed by install_lang helpers.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        build-essential \
        curl \
        libzmq3-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Jupyter so tests can execute notebooks; everything else is handled at runtime.
WORKDIR /workspace
COPY . /opt/bridgeit-src
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir \
        jupyterlab \
        nbclient \
        /opt/bridgeit-src \
    && rm -rf /opt/bridgeit-src

# Default command drops into shell; mount the repository at /workspace when running.
CMD ["bash"]
