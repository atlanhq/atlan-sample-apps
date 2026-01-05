from __future__ import annotations

from typing import Any, Dict

from app.handlers.dq_poc import start_dq_poc as start_dq_poc_handler
from app.models import DqPocRequest
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.server.fastapi import APIServer
from fastapi import Body
from fastapi.routing import APIRouter

logger = get_logger(__name__)


def register_custom_routes(server: APIServer) -> None:
    """
    Add custom endpoints to the default SDK FastAPI server.

    This keeps the SDK endpoints untouched (ex: POST /workflows/v1/start) while
    adding a custom route that can accept/return any payload you want.
    """

    router = APIRouter()

    async def start_dq_poc(
        body: DqPocRequest = Body(...),
    ) -> Dict[str, Any]:
        return await start_dq_poc_handler(server=server, body=body)

    router.add_api_route(
        "/dq-poc",
        start_dq_poc,
        methods=["POST"],
    )

    # Mount once under /api/v1 and also as an alias under /workflows/v1
    server.app.include_router(router, prefix="/workflows/v1")

    logger.info("Registered custom dq-poc routes")
