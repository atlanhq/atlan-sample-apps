# syntax=docker/dockerfile:1
# Dockerfile for generic connector
#
# Extends the app-runtime-base image with the connector code and dependencies.
#
# Build args:
#   APP_MODULE - Python module path; baked into ATLAN_APP_MODULE env var
#
# Usage:
#   docker build \
#     --build-arg APP_MODULE=app.connector:GenericConnector \
#     -t generic:latest .

FROM registry.atlan.com/public/app-runtime-base:3

ARG APP_MODULE=app.connector:GenericConnector

WORKDIR /app

# Copy lock files first for dependency caching
COPY --chown=appuser:appuser pyproject.toml uv.lock* ./

# Install dependencies (excluding the project itself) into a new venv
RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv venv .venv && \
    uv sync --no-install-project --no-dev

# Copy application code
COPY --chown=appuser:appuser app/ app/

ENV ATLAN_APP_MODULE=${APP_MODULE}
ENV ATLAN_CONTRACT_GENERATED_DIR=/app/app/generated
