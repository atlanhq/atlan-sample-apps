# Application SDK Chainguard base image with Python, Dapr, and application-sdk pre-installed
FROM ghcr.io/atlanhq/application-sdk-chainguard-image:latest

# Default working directory (already set in base image)
WORKDIR /app

# Install dependencies first (better caching)
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv sync --locked --no-install-project

# Copy application code
COPY --chown=appuser:appuser . .

# App-specific environment variables
ENV ATLAN_APP_HTTP_PORT=8000

# Download DAPR components and set up entrypoint
RUN uv run poe download-components

ENTRYPOINT ["sh", "-c", "dapr run --log-level info --app-id app --scheduler-host-address '' --placement-host-address '' --max-body-size 1024Mi --app-port $ATLAN_APP_HTTP_PORT --dapr-http-port $ATLAN_DAPR_HTTP_PORT --dapr-grpc-port $ATLAN_DAPR_GRPC_PORT --metrics-port $ATLAN_DAPR_METRICS_PORT --resources-path /app/components uv run main.py"]