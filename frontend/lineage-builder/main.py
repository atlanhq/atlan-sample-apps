import asyncio
import os

os.environ["ATLAN_APPLICATION_NAME"] = "atlan-embedded-lineage-builder"

from application_sdk.application import BaseApplication
from application_sdk.constants import APPLICATION_NAME
from application_sdk.server.fastapi import APIServer
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# LOCAL DEV ONLY — Reverse proxy for /api/meta/*
#
# In production (deployed inside Atlan), the platform routes /api/meta/*
# natively — this proxy is not needed or registered.
#
# Enable with:
#   DEV_MODE=true ATLAN_BASE_URL=https://fs3.atlan.com uv run main.py
# ---------------------------------------------------------------------------


def register_dev_proxy(fastapi_app):
    import httpx
    from fastapi import Request
    from fastapi.responses import StreamingResponse

    atlan_base_url = os.environ["ATLAN_BASE_URL"].rstrip("/")
    logger.info(f"[DEV PROXY] /api/meta/* → {atlan_base_url}")

    @fastapi_app.api_route(
        "/api/meta/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
    )
    async def proxy_meta_api(request: Request, path: str):
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
                content=await request.body()
                if request.method in ("POST", "PUT")
                else None,
            )

        return StreamingResponse(
            iter([upstream.content]),
            status_code=upstream.status_code,
            headers={
                "content-type": upstream.headers.get(
                    "content-type", "application/json"
                ),
            },
        )


async def main():
    logger.info("Starting Manual Lineage Builder application")

    server = APIServer()

    dev_mode = os.environ.get("DEV_MODE", "").lower() == "true"
    if dev_mode and os.environ.get("ATLAN_BASE_URL"):
        register_dev_proxy(server.app)

    application = BaseApplication(name=APPLICATION_NAME, server=server)
    await application.start_server()


if __name__ == "__main__":
    asyncio.run(main())
