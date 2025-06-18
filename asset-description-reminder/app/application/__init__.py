from app.handlers import AssetDescriptionHandler
from application_sdk.application import BaseApplication
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.server.fastapi.models import HandlerRoute

logger = get_logger(__name__)

class AssetDescriptionReminderApplication(BaseApplication):
    def __init__(
        self,
        name: str = "asset-description-reminder",
    ):
        handler = AssetDescriptionHandler()

        self.handler_routes = [
            HandlerRoute(
                path="/users",
                handler_method=handler.get_users,
                methods=["POST"],
            ),
        ]

        # Initialize base with handler
        super().__init__(name=name, handler=handler)

    async def setup_api_server(self):
        # Make sure server is ready before registering routes
        if not self.server:
            raise ValueError("Server not initialized")

        await self.register_handler_routes(self.handler_routes)
