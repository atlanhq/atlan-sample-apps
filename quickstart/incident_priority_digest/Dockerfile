# Base image from application-sdk (includes Python, uv, Dapr, appuser, entrypoint)
FROM registry.atlan.com/public/application-sdk:main-2.3.1

# Install dependencies first (better caching)
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv venv .venv && \
    uv sync --locked --no-install-project

# Copy application code
COPY --chown=appuser:appuser . .

# Set app port (used by entrypoint.sh)
ENV ATLAN_APP_HTTP_PORT=8000

# Download DAPR components
RUN uv run poe download-components
