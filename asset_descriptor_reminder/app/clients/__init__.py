from typing import Any, Dict, Optional

import requests
from application_sdk.clients import ClientInterface
from pyatlan.client.atlan import AtlanClient
from slack_sdk import WebClient


class AssetDescriptionClient(ClientInterface):
    def __init__(self):
        self.atlan_client: Optional[AtlanClient] = None
        self.slack_client: Optional[WebClient] = None
        self.credentials: Optional[Dict[str, str]] = None

    async def load(self, credentials: Dict[str, Any]) -> None:
        """Load and establish connections to Atlan and Slack."""
        self.credentials = credentials

        if not self.credentials.get("base_url") or not self.credentials.get(
            "atlan_token"
        ):
            raise ValueError(
                "Missing required Atlan credentials (base_url and atlan_token)"
            )

        self.atlan_client = AtlanClient(
            base_url=self.credentials["base_url"],
            api_key=self.credentials["atlan_token"],
        )

        if self.credentials.get("slack_bot_token"):
            self.slack_client = WebClient(token=self.credentials["slack_bot_token"])

    async def close(self) -> None:
        """Cleanup connections"""
        if self.atlan_client:
            self.atlan_client = None

        self.slack_client = None
        self.credentials = None

    async def get_atlan_client(self) -> AtlanClient:
        """Get the Atlan client instance."""
        if not self.atlan_client and self.credentials:
            await self.load(self.credentials)
        elif not self.credentials:
            raise ValueError(
                "Client not initialized - call load() with credentials first"
            )

        return self.atlan_client

    async def get_slack_client(self) -> Optional[WebClient]:
        """Get the Slack client instance."""
        if (
            not self.slack_client
            and self.credentials
            and self.credentials.get("slack_bot_token")
        ):
            await self.load(self.credentials)
        elif not self.credentials:
            raise ValueError(
                "Client not initialized - call load() with credentials first"
            )
        return self.slack_client

    async def get(
        self, url: str, params: Dict[str, Any], bearer: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make a GET request with optional bearer token."""
        headers = {"Content-Type": "application/json"}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
