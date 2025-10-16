# Wolfi base image with Python
FROM cgr.dev/chainguard/wolfi-base

# Build-time argument to select which app (directory with its own pyproject.toml)
# Example usage: --build-arg APP_PATH=quickstart/hello_world
ARG APP_PATH="."

# Switch back to root for system installations
USER root

# Install system dependencies
RUN apk add --no-cache \
    curl \
    bash \
    libstdc++ \
    git \
    gcc \
    python3-dev \
    && rm -rf /var/cache/apk/*

# Copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser

# Set up directories and switch to appuser early
RUN mkdir -p /app /home/appuser/.local/bin /home/appuser/.cache/uv && \
    chown -R appuser:appuser /app /home/appuser

WORKDIR /app
USER appuser

# Install dependencies first (better caching)
COPY --chown=appuser:appuser ${APP_PATH}/pyproject.toml ${APP_PATH}/uv.lock ./
RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv venv .venv && \
    uv sync --locked --no-install-project

# Copy application code for the selected app
COPY --chown=appuser:appuser ${APP_PATH}/ .

# Switch back to root for system installations
USER root

# Install Dapr CLI
RUN curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | DAPR_INSTALL_DIR="/usr/local/bin" /bin/bash -s 1.14.1

# Download DAPR components and set up entrypoint
RUN uv run poe download-components

# Remove curl and bash
RUN apk del curl bash

# Switch back to appuser for application operations
USER appuser

ENV ATLAN_DAPR_HTTP_PORT=3500 \
    ATLAN_DAPR_GRPC_PORT=50001 \
    ATLAN_DAPR_METRICS_PORT=3100 \
    ATLAN_APP_HTTP_PORT=8000 \
    UV_CACHE_DIR=/home/appuser/.cache/uv \
    XDG_CACHE_HOME=/home/appuser/.cache

ENV UV_CACHE_DIR=/home/appuser/.cache/uv \
    XDG_CACHE_HOME=/home/appuser/.cache


RUN dapr init --slim --runtime-version=1.14.4

ENTRYPOINT ["sh", "-c", "dapr run --log-level info --app-id app --scheduler-host-address '' --app-port $ATLAN_APP_HTTP_PORT --dapr-http-max-request-size 1024 --dapr-http-port $ATLAN_DAPR_HTTP_PORT --dapr-grpc-port $ATLAN_DAPR_GRPC_PORT --metrics-port $ATLAN_DAPR_METRICS_PORT --resources-path /app/components uv run main.py"]