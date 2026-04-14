# Standalone Dockerfile — this app is a lightweight FastAPI server,
# not an SDK-based app, so it skips Dapr/poe/components entirely.
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
