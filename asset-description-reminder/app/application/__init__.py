from typing import Any, Dict, List, Optional

from app.clients import AssetDescriptionClient
from app.handlers import AssetDescriptionHandler
from application_sdk.application import BaseApplication
from application_sdk.observability import observability
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.server.fastapi.models import HandlerRoute
from pydantic import BaseModel

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


class UserCredentials(BaseModel):
    base_url: str
    atlan_token: str
    slack_bot_token: str


class AssetDescriptionReminderApplication(BaseApplication):
    def __init__(
        self,
        name: str = "asset-description-reminder",
    ):
        handler = AssetDescriptionHandler()

        # Create routes before super().__init__
        self.handler_routes = [
            HandlerRoute(
                path="/users",
                handler_method=handler.get_users,
                methods=["POST"],
                request_model=UserCredentials,
            )
        ]

        # Initialize base with handler
        super().__init__(name=name, handler=handler)

    async def setup_api_server(self):
        # Make sure server is ready before registering routes
        if not self.server:
            raise ValueError("Server not initialized")

        await self.register_handler_routes(self.handler_routes)
