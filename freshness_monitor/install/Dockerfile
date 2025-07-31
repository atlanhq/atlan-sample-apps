# Install uv
FROM python:3.11-slim

# Install git (and optionally build-essential if you have other build dependencies)
# Note: this is required for uv's git-based dependency resolution to work
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Create directories with proper permissions
RUN mkdir -p /app /home/appuser/.cache/uv && \
    chown -R appuser:appuser /app /home/appuser

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies as root first
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml

# Copy the project into the image
ADD . /app

# Create virtual environment and sync dependencies as root
RUN uv venv .venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Set proper ownership for the entire app directory and venv
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables for uv cache
ENV UV_CACHE_DIR=/home/appuser/.cache/uv
ENV XDG_CACHE_HOME=/home/appuser/.cache

# Set the entrypoint
ENTRYPOINT ["uv", "run", "/app/main.py"]
