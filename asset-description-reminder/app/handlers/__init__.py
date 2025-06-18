"""
Handler for Asset Description Reminder operations.

This module provides the handler for interacting with Atlan and Slack APIs.
"""

import os
from typing import Any, Dict

from app.clients import AssetDescriptionClient
from application_sdk.handlers import HandlerInterface
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class AssetDescriptionHandler(HandlerInterface):
    """Handler for asset description reminder operations.

    This handler manages interactions with Atlan and Slack APIs through the AssetDescriptionClient.
    """

    def __init__(self):
        """Initialize the handler with a client."""
        self.client = AssetDescriptionClient()

    async def load(self, credentials: Dict[str, Any]) -> None:
        """Mock loading credentials.

        Args:
            credentials (Dict[str, Any]): Credentials for API access.
        """
        await self.client.load(credentials)

    async def test_auth(self) -> bool:
        """Mock authentication test"""
        logger.info("Mock: Testing authentication")
        return True

    async def preflight_check(self) -> bool:
        """Mock preflight checks"""
        logger.info("Mock: Running preflight checks")
        return True

    async def fetch_metadata(self) -> None:
        """Not used in this handler"""
        pass

    async def get_users(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of users in the tenant by calling the admin API directly.

        Args:
            credentials: The request body containing API credentials

        Returns:
            Dict[str, Any]: Dictionary containing list of users

        Raises:
            ValueError: If required environment variables are not set.
        """
        logger.info("get_users handler method called")
        await self.load(credentials)

        response = await self.client.get(
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
