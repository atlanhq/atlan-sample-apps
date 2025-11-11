# Wolfi base image with Python
FROM junaidrahimatlan/application-sdk-chainguard:latest

USER root

RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser

RUN mkdir -p /app /home/appuser/.local/bin /home/appuser/.cache/uv && \
    chown -R appuser:appuser /app /home/appuser

WORKDIR /app

USER appuser

COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./

COPY --chown=appuser:appuser . .

USER appuser

ENV ATLAN_DAPR_HTTP_PORT=3500 \
    ATLAN_DAPR_GRPC_PORT=50001 \
    ATLAN_DAPR_METRICS_PORT=3100 \
    ATLAN_APP_HTTP_PORT=8000 \
    UV_CACHE_DIR=/home/appuser/.cache/uv \
    XDG_CACHE_HOME=/home/appuser/.cache

ENV UV_CACHE_DIR=/home/appuser/.cache/uv \
    XDG_CACHE_HOME=/home/appuser/.cache

# Download DAPR components and set up entrypoint
RUN uv run poe download-components

RUN dapr init --slim --runtime-version=1.16.0

RUN rm /home/appuser/.dapr/bin/dashboard /home/appuser/.dapr/bin/placement /home/appuser/.dapr/bin/scheduler

ENTRYPOINT ["sh", "-c", "dapr run --log-level info --app-id app --scheduler-host-address '' --placement-host-address '' --max-body-size 1024Mi --app-port $ATLAN_APP_HTTP_PORT --dapr-http-port $ATLAN_DAPR_HTTP_PORT --dapr-grpc-port $ATLAN_DAPR_GRPC_PORT --metrics-port $ATLAN_DAPR_METRICS_PORT --resources-path /app/components uv run main.py"]