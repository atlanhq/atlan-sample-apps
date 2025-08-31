FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user early
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Set up directories and switch to appuser early
RUN mkdir -p /app /home/appuser/.cache/uv /home/appuser/logs /home/appuser/runtime && \
    chown -R appuser:appuser /app /home/appuser

WORKDIR /app
USER appuser

# Install dependencies first (better caching)
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv venv .venv && \
    uv sync --locked --no-install-project

# Copy application code
COPY --chown=appuser:appuser . .

# Switch back to root for system installations
USER root

# Install Dapr CLI and Supervisor
RUN curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | DAPR_INSTALL_DIR="/usr/local/bin" /bin/bash -s 1.14.1 && \
    pip install --no-cache-dir supervisor

# Copy supervisor config
COPY ./deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV ATLAN_DAPR_APP_PORT=3000 \
    ATLAN_DAPR_HTTP_PORT=3500 \
    ATLAN_DAPR_GRPC_PORT=50001 \
    ATLAN_DAPR_METRICS_PORT=3100 \
    UV_CACHE_DIR=/home/appuser/.cache/uv \
    XDG_CACHE_HOME=/home/appuser/.cache

# Switch back to appuser for application operations
USER appuser

# Download DAPR components and set up entrypoint
RUN uv run poe download-components

# Copy and set executable entrypoint with line ending fix
COPY --chown=appuser:appuser ./deploy/entrypoint.sh /app/entrypoint.sh
USER root
RUN chmod +x /app/entrypoint.sh && \
    # Fix potential Windows line endings
    sed -i 's/\r$//' /app/entrypoint.sh
USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]