import asyncio
import os

# Set the application name before importing SDK constants
os.environ["ATLAN_APPLICATION_NAME"] = "metadata-lens"

from application_sdk.application import BaseApplication
from application_sdk.constants import APPLICATION_NAME
from application_sdk.server.fastapi import APIServer
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


# ---------------------------------------------------------------------------
# LOCAL DEV ONLY — Reverse proxy for /api/meta/*
#
# When running locally, the frontend's API calls to /api/meta/* need to reach
# the real Atlan instance. In production (deployed inside Atlan), these calls
# are handled by the platform's own routing — this proxy is not needed.
#
# Enable by setting BOTH env vars:
#   DEV_MODE=true ATLAN_BASE_URL=https://your-tenant.atlan.com uv run main.py
#
# DEV_MODE is the gate — ATLAN_BASE_URL alone does NOT activate the proxy,
# since ATLAN_BASE_URL is injected by the CI/CD system in production.
# ---------------------------------------------------------------------------


def register_dev_proxy(fastapi_app):
    """Register a reverse proxy route for local development.

    This is NOT used in production. It forwards /api/meta/* requests to the
    Atlan instance specified by ATLAN_BASE_URL, attaching the Authorization
    header from the incoming request.
    """
    import httpx
    from fastapi import Request
    from fastapi.responses import StreamingResponse

    atlan_base_url = os.environ["ATLAN_BASE_URL"].rstrip("/")

    logger.info(
        f"[DEV PROXY] Enabled — /api/meta/* will be forwarded to {atlan_base_url}"
    )

    @fastapi_app.api_route("/api/meta/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def proxy_meta_api(request: Request, path: str):
        """Forward /api/meta/* requests to the Atlan instance.

        Local dev only — in production, these routes don't exist because the
        platform handles /api/meta/* natively.
        """
        target_url = f"{atlan_base_url}/api/meta/{path}"
        if request.url.query:
            target_url += f"?{request.url.query}"

        headers = {}
        if "authorization" in request.headers:
            headers["Authorization"] = request.headers["authorization"]
        headers["Accept"] = request.headers.get("accept", "application/json")

        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body() if request.method in ("POST", "PUT") else None,
            )

        return StreamingResponse(
            iter([upstream.content]),
            status_code=upstream.status_code,
            headers={
                "content-type": upstream.headers.get("content-type", "application/json"),
            },
        )


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    logger.info("Starting MetadataLens application")

    server = APIServer()

    # --- LOCAL DEV ONLY: register proxy if DEV_MODE is explicitly set ---
    dev_mode = os.environ.get("DEV_MODE", "").lower() == "true"
    if dev_mode and os.environ.get("ATLAN_BASE_URL"):
        register_dev_proxy(server.app)
    # -------------------------------------------------------------------

    application = BaseApplication(name=APPLICATION_NAME, server=server)

    await application.start_server()


if __name__ == "__main__":
    asyncio.run(main())
