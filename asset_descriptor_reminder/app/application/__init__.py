from application_sdk.application import BaseApplication
from typing import Any, Dict
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.server.fastapi import APIServer, HttpWorkflowTrigger
from app.clients import AssetDescriptionClient
from fastapi import APIRouter
from fastapi import Body
from pydantic import BaseModel

logger = get_logger(__name__)

class GetUsersRequest(BaseModel):
    base_url: str
    atlan_token: str
    slack_bot_token: str

class AssetDescriptionServer(APIServer):
    async def get_users(self, body: GetUsersRequest = Body(...)) -> Dict[str, Any]:
        """Get list of users in the tenant by calling the admin API directly.

        Args:
            credentials: The request body containing API credentials

        Returns:
            Dict[str, Any]: Dictionary containing list of users

        Raises:
            ValueError: If required environment variables are not set.
        """
        logger.info("get_users handler method called")
        credentials = body.model_dump()
        client = AssetDescriptionClient()
        await client.load(credentials)
        
        response = await client.get(
            url=f"{credentials['base_url']}/api/service/users",
            params={
                "limit": 100,
                "offset": 0,
                "sort": "firstName",
                "columns": ["firstName", "lastName", "username", "email"]
            },
            bearer=credentials['atlan_token']
        )

        users = [
            {
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "firstName": user.get("firstName", ""),
                "lastName": user.get("lastName", ""),
                "displayName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
            }
            for user in response.get("records", [])
            if user.get("username")
        ]

        return {
            "success": True,
            "users": users
        }
        
    def register_routes(self):
        app_router = APIRouter()
        app_router.add_api_route(
            path="/users",
            endpoint=self.get_users,
            methods=["POST"],
        )
        
        self.app.include_router(app_router, prefix="/api/v1")
        
        super().register_routes()

class AssetDescriptionApplication(BaseApplication):
    def __init__(self, name: str):
        super().__init__(name)

    async def setup_server(self, workflow_class):
        """
        Set up the FastAPI server for the SQL metadata extraction application.

        Args:
            workflow_class (Type): Workflow class to register with the server. Defaults to BaseSQLMetadataExtractionWorkflow.

        Returns:
            Any: None
        """
        if self.workflow_client is None:
            await self.workflow_client.load()

        # setup application server. serves the UI, and handles the various triggers
        self.server = AssetDescriptionServer(
            workflow_client=self.workflow_client,
        )

        # register the workflow on the application server
        # the workflow is by default triggered by an HTTP POST request to the /start endpoint
        self.server.register_workflow(
            workflow_class=workflow_class,
            triggers=[HttpWorkflowTrigger()],
        )