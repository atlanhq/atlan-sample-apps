"""
Connector Client - API Client for Your Data Source

This client handles communication with your external data source.
Extend the `load()` method to set up authentication and configure headers.
Add methods to fetch data from your source APIs.

Example sources: REST APIs, GraphQL endpoints, databases, etc.
"""

from typing import Any, Dict, List

from application_sdk.clients.base import BaseClient
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class ConnectorClient(BaseClient):
    """
    Client for interacting with your data source.

    TODO: Customize this client for your specific data source.
    - Update load() with your authentication logic
    - Add methods to fetch metadata from your source
    """

    async def load(self, **kwargs: Any) -> None:
        """
        Initialize the client with credentials and configuration.

        This method is called by the SDK before any API operations.
        Use it to:
        - Extract credentials from kwargs
        - Set up authentication headers
        - Initialize any required client state

        Args:
            **kwargs: Contains 'credentials' dict with values from the UI form.
        """
        credentials = kwargs.get("credentials", {})
        self.credentials = credentials

        # Extract configuration from credentials
        self.host = credentials.get("host", "")
        extra = credentials.get("extra", {})
        self.source_name = extra.get("source_name", "my-source")

        # Set up HTTP headers for API calls
        self.http_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Atlan-Connector",
            # TODO: Add authentication headers if needed
            # "Authorization": f"Bearer {self.api_key}",
        }

        logger.info(f"Client initialized for source: {self.source_name}, host: {self.host}")

    async def fetch_metadata(self) -> List[Dict[str, Any]]:
        """
        Fetch metadata from your data source.

        TODO: Implement your metadata extraction logic here.

        Returns:
            List[Dict[str, Any]]: List of metadata records.

        Example implementation:
            url = f"{self.base_url}/api/resources"
            response = await self.execute_http_get_request(url)
            if response and response.is_success:
                return response.json()
            return []
        """
        # -----------------------------------------------------------------
        # PLACEHOLDER: Returns stub data for template demonstration
        # Replace this with actual API calls to your data source
        # -----------------------------------------------------------------
        logger.info("Fetching metadata from source (placeholder)")

        stub_data = [
            {
                "id": "item-001",
                "name": "Sample Item 1",
                "type": "resource",
                "description": "This is a sample item",
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "item-002",
                "name": "Sample Item 2",
                "type": "resource",
                "description": "This is another sample item",
                "created_at": "2024-01-02T00:00:00Z",
            },
        ]

        logger.info(f"Fetched {len(stub_data)} items (placeholder data)")
        return stub_data

    async def verify_connection(self) -> bool:
        """
        Verify connectivity to the data source.

        TODO: Implement a lightweight check to verify the connection works.

        Returns:
            bool: True if connection is successful.
        """
        # -----------------------------------------------------------------
        # PLACEHOLDER: Always returns True for template
        # Replace with actual connection verification
        # Example:
        #   response = await self.execute_http_get_request(f"{self.base_url}/health")
        #   return response is not None and response.is_success
        # -----------------------------------------------------------------
        logger.info("Verifying connection (placeholder - always succeeds)")
        return True
