from typing import Optional, Dict, Any
from application_sdk.clients import ClientInterface
from pyatlan.client.atlan import AtlanClient
from slack_sdk import WebClient
import requests
import os

class AssetDescriptionClient(ClientInterface):
    def __init__(self):
        self.atlan_client: Optional[AtlanClient] = None
        self.slack_client: Optional[WebClient] = None

    async def load(self) -> None:
        """Load and establish connections to Atlan and Slack.

        Args:
            credentials (Dict[str, Any]): Connection credentials containing:
                - base_url: Atlan base URL (or from env ATLAN_BASE_URL)
                - api_key: Atlan API key (or from env ATLAN_API_KEY)
                - slack_token: Optional Slack bot token (or from env SLACK_BOT_TOKEN)
        """
        # Initialize Atlan client
        base_url = os.getenv("ATLAN_BASE_URL")
        api_key = os.getenv("ATLAN_API_KEY")

        if not base_url or not api_key:
            raise ValueError("Missing required Atlan credentials")

        self.atlan_client = AtlanClient(
            base_url=base_url,
            api_key=api_key
        )
        AtlanClient.set_current_client(self.atlan_client)

        # Initialize Slack client if token provided
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if slack_token:
            self.slack_client = WebClient(token=slack_token)


    async def close(self) -> None:
        """Cleanup connections"""
        if self.atlan_client:
            AtlanClient.set_current_client(None)
            self.atlan_client = None

        self.slack_client = None

    def get_atlan_client(self) -> AtlanClient:
        """Get the Atlan client instance.

        Returns:
            AtlanClient: The initialized Atlan client

        Raises:
            ValueError: If client not initialized
        """
        if not self.atlan_client:
            raise ValueError("Atlan client not initialized. Call load() first.")
        AtlanClient.set_current_client(self.atlan_client)
        return self.atlan_client

    def get_slack_client(self) -> Optional[WebClient]:
        """Get the Slack client instance.

        Returns:
            Optional[WebClient]: The initialized Slack client or None if not configured
        """
        if not self.slack_client:
            raise ValueError("Slack client not initialized. Call load() first.")
        return self.slack_client

    async def get(self, url: str, params: Dict[str, Any], bearer: Optional[str] = None) -> Dict[str, Any]:
        """Make a GET request with optional bearer token.

        Args:
            url (str): Request URL
            params (Dict[str, Any]): Query parameters
            bearer (Optional[str]): Bearer token for authorization

        Returns:
            Dict[str, Any]: JSON response

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        headers = {
            "Content-Type": "application/json"
        }
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()