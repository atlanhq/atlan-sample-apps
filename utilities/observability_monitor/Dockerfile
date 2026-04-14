# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-build

WORKDIR /app
COPY frontend/ui/package.json frontend/ui/package-lock.json frontend/ui/
RUN cd frontend/ui && npm ci
COPY frontend/ui/ frontend/ui/
RUN cd frontend/ui && npm run build
# Output: /app/frontend/static/assets/index.{js,css}

# Stage 2: App Framework base image (includes Python, uv, Dapr, appuser, entrypoint)
FROM registry.atlan.com/public/application-sdk:main-2.6.0

# Install dependencies first (better caching)
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv venv .venv && \
    uv sync --locked --no-install-project

# Copy application code
COPY --chown=appuser:appuser . .

# Copy built frontend assets from Stage 1
COPY --from=frontend-build --chown=appuser:appuser /app/frontend/static/ frontend/static/

# Set app port (used by entrypoint.sh)
ENV ATLAN_APP_HTTP_PORT=8000

# Download Dapr components
RUN uv run poe download-components
