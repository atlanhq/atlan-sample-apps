from application_sdk.application import BaseApplication
from application_sdk.server.fastapi.models import HandlerRoute
from application_sdk.observability import observability
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from app.handlers import AssetDescriptionHandler
from app.clients import AssetDescriptionClient

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


class AssetDescriptionReminderApplication(BaseApplication):
    def __init__(self, name: str = "asset-description-reminder", client: Optional[AssetDescriptionClient] = None):
        self.client = client
        if not self.client:
            raise ValueError("Client is required")
        
        handler = AssetDescriptionHandler(client=self.client)
        
        # Create routes before super().__init__
        self.handler_routes = [
            HandlerRoute(
                path="/users",
                handler_method=handler.get_users,
                methods=["GET"],
            )
        ]
        
        # Initialize base with handler
        super().__init__(name=name, handler=handler)

    async def setup_api_server(self):
        # Make sure server is ready before registering routes
        if not self.server:
            raise ValueError("Server not initialized")
            
        await self.register_handler_routes(self.handler_routes)