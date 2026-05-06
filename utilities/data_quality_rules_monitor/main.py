import asyncio
import os

os.environ["ATLAN_APPLICATION_NAME"] = "data-quality-rules-monitor"

from application_sdk.application import BaseApplication
from application_sdk.constants import APPLICATION_NAME
from application_sdk.server.fastapi import APIServer
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)

# CORS headers returned for every preflight and proxied response.
# "null" is the origin sent by sandboxed iframes; "*" covers same-origin and
# direct browser access.  We restrict to /api/meta/* paths in the proxy itself.
_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, content-type, accept",
    "Access-Control-Max-Age": "86400",
}


def register_api_proxy(fastapi_app):
    """Proxy /api/meta/* and /api/service/* to the Atlan backend.

    Embedded apps are loaded in sandboxed iframes whose origin is "null".
    Direct browser fetch to the Atlan API fails the CORS preflight (OPTIONS
    returns 302 → login.jsp).  Routing through this proxy lets the app handle
    the preflight correctly and forward the user's Bearer token upstream.
    """
    import httpx
    from fastapi import Request
    from fastapi.responses import JSONResponse, StreamingResponse

    atlan_base_url = os.environ["ATLAN_BASE_URL"].rstrip("/")
    logger.info(f"[PROXY] /api/meta/* and /api/service/* -> {atlan_base_url}")

    async def _proxy(request: Request, api_prefix: str, path: str):
        # Handle CORS preflight without forwarding upstream.
        if request.method == "OPTIONS":
            return JSONResponse(content={}, headers=_CORS_HEADERS)

        target_url = f"{atlan_base_url}/{api_prefix}/{path}"
        if request.url.query:
            target_url += f"?{request.url.query}"

        headers = {"Accept": request.headers.get("accept", "application/json")}
        if "authorization" in request.headers:
            headers["Authorization"] = request.headers["authorization"]

        body = await request.body() if request.method in ("POST", "PUT", "PATCH") else None

        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

        response_headers = {
            "content-type": upstream.headers.get("content-type", "application/json"),
            **_CORS_HEADERS,
        }
        return StreamingResponse(
            iter([upstream.content]),
            status_code=upstream.status_code,
            headers=response_headers,
        )

    @fastapi_app.api_route(
        "/api/meta/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    async def proxy_meta_api(request: Request, path: str):
        return await _proxy(request, "api/meta", path)

    @fastapi_app.api_route(
        "/api/service/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    async def proxy_service_api(request: Request, path: str):
        return await _proxy(request, "api/service", path)


async def main():
    logger.info("Starting Data Quality Rules Monitor")

    server = APIServer()

    # Register the API proxy whenever ATLAN_BASE_URL is available (i.e. always
    # in production).  This routes browser fetch calls from the sandboxed iframe
    # through this backend, avoiding the CORS preflight failure that occurs when
    # the browser calls the Atlan API directly.
    if os.environ.get("ATLAN_BASE_URL"):
        register_api_proxy(server.app)

    application = BaseApplication(name=APPLICATION_NAME, server=server)
    await application.start_server()


if __name__ == "__main__":
    asyncio.run(main())
