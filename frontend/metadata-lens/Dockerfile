# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-build

WORKDIR /app
COPY frontend/ui/package.json frontend/ui/package-lock.json frontend/ui/
RUN cd frontend/ui && npm ci
COPY frontend/ui/ frontend/ui/
RUN cd frontend/ui && npm run build
# Output: /app/frontend/static/assets/index.{js,css}

# Stage 2: Python application
FROM cgr.dev/chainguard/wolfi-base

# Switch back to root for system installations
USER root
# Install system dependencies
RUN apk add --no-cache \
    libstdc++ \
    git \
    gcc \
    python3-dev \
    curl \
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
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv venv .venv && \
    uv sync --locked --no-install-project

# Copy application code (excludes frontend/static via .dockerignore)
COPY --chown=appuser:appuser . .

# Copy built frontend assets from Stage 1
COPY --from=frontend-build --chown=appuser:appuser /app/frontend/static/ frontend/static/

ENV ATLAN_APP_HTTP_PORT=8000 \
    UV_CACHE_DIR=/home/appuser/.cache/uv \
    XDG_CACHE_HOME=/home/appuser/.cache

# No Dapr — this is a frontend-only app. The application-sdk serves the
# built React frontend via FastAPI directly.
ENTRYPOINT ["uv", "run", "main.py"]
