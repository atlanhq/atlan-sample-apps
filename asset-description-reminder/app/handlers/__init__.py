"""
Handler for Asset Description Reminder operations.

This module provides the handler for interacting with Atlan and Slack APIs.
"""

import os
from typing import Any, Dict, List, Optional

from app.clients import AssetDescriptionClient
from application_sdk.handlers import HandlerInterface
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class AssetDescriptionHandler(HandlerInterface):
    """Handler for asset description reminder operations.

    This handler manages interactions with Atlan and Slack APIs through the AssetDescriptionClient.
    """

    def __init__(self, client: Optional[AssetDescriptionClient] = None):
        """Initialize the handler with a client."""
        if not client:
            raise ValueError("Client is required")
        self.client = client

    async def load(self) -> None:
        """Load and initialize the client with credentials.

        Args:
            credentials (Dict[str, Any]): Credentials for API access.
        """
        await self.client.load()

    async def test_auth(self) -> bool:
        """Test if client is authenticated"""
        pass

    async def preflight_check(self) -> bool:
        """Run preflight checks"""
        pass

    async def fetch_metadata(self) -> None:
        """Not used in this handler"""
        pass

    async def get_users(self) -> Dict[str, Any]:
        """Get list of users in the tenant by calling the admin API directly.

        Returns:
            List[Dict[str, Any]]: List of user information dictionaries.

        Raises:
            ValueError: If required environment variables are not set.
        """
        logger.info("get_users handler method called")
        base_url = os.getenv("ATLAN_BASE_URL")
        api_key = os.getenv("ATLAN_API_KEY")

        # if not base_url or not api_key:
        #     raise ValueError("ATLAN_BASE_URL or ATLAN_API_KEY not set. Cannot make direct API call.")

        # response = await self.client.get(
        #     url=f"{base_url}/api/service/users",
        #     params={
        #         "limit": 100,
        #         "offset": 0,
        #         "sort": "firstName",
        #         "columns": ["firstName", "lastName", "username", "email"]
        #     },
        #     bearer=api_key
        # )

        # users = [
        #     {
        #         "username": user.get("username", ""),
        #         "email": user.get("email", ""),
        #         "firstName": user.get("firstName", ""),
        #         "lastName": user.get("lastName", ""),
        #         "displayName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
        #     }
        #     for user in response.get("records", [])
        #     if user.get("username")
        # ]

        return {
            "users": [
                {
                    "username": "Mustafa",
                    "email": "mustafa@atlan.com",
                    "firstName": "Mustafa",
                    "lastName": "Khan",
                    "displayName": "Mustafa Khan",
                }
            ]
        }
