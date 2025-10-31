# Wolfi base image with Python
FROM cgr.dev/chainguard/wolfi-base

# Switch to root for system installations
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

# Set up directories and switch to appuser
RUN mkdir -p /app /home/appuser/.local/bin /home/appuser/.cache/uv && \
    chown -R appuser:appuser /app /home/appuser

WORKDIR /app
USER appuser

# Install dependencies first (better caching)
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv venv .venv && \
    uv sync --locked --no-install-project

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser frontend/ ./frontend/
COPY --chown=appuser:appuser main.py ./

# Switch back to root to remove curl and bash (security)
USER root
RUN apk del curl bash && rm -rf /var/cache/apk/*

# Switch back to appuser for runtime
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/home/appuser/.cache/uv \
    XDG_CACHE_HOME=/home/appuser/.cache

# Expose application port
EXPOSE 8000

# Run the application (Dapr sidecar injected by Kubernetes)
CMD ["uv", "run", "main.py"]

