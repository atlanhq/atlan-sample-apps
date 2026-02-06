"""
Connector Handler - FastAPI Request Handlers

This handler provides endpoints for the UI wizard:
- test_auth: Validates credentials
- fetch_metadata: Returns data for filter dropdowns
- preflight_check: Validates configuration before workflow starts
- get_configmap: Returns UI configuration JSON
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from app.clients import ConnectorClient
from application_sdk.handlers.base import BaseHandler
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class ConnectorHandler(BaseHandler):
    """
    Handler for UI interactions and preflight checks.

    The SDK automatically:
    - Calls load() on the client with credentials before each method
    - Wraps responses in standard format {"success": bool, "data": ...}
    """

    def __init__(self, client: ConnectorClient | None = None):
        super().__init__(client=client)
        self.client: ConnectorClient | None = client

    async def test_auth(self) -> bool:
        """
        Test authentication credentials.

        Called when user clicks "Test Connection" in the UI.

        Returns:
            bool: True if authentication succeeds.
        """
        try:
            if not self.client:
                logger.error("Client not initialized")
                return False

            result = await self.client.verify_connection()
            logger.info(f"Authentication test result: {result}")
            return result

        except Exception as e:
            logger.error(f"Authentication test failed: {e}")
            return False

    async def fetch_metadata(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Fetch metadata for UI filter dropdowns.

        Called when user reaches the metadata selection page.

        Returns:
            List[Dict[str, Any]]: Hierarchical structure for tree selector.
                Format: [{"value": "id", "title": "display", "children": [...]}]
        """
        try:
            if not self.client:
                return []

            # -----------------------------------------------------------------
            # TODO: Fetch real metadata and format for UI tree selector
            # -----------------------------------------------------------------
            logger.info("Fetching metadata for UI")

            # Placeholder: Return simple structure
            return [
                {"value": "all", "title": "All Resources", "children": []},
            ]

        except Exception as e:
            logger.error(f"Failed to fetch metadata: {e}")
            return []

    async def preflight_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration before workflow starts.

        Called when user clicks "Start" or runs preflight check.

        Args:
            payload: Full request body with 'credentials' and 'metadata' fields.

        Returns:
            Dict with check results in format:
            {"checkName": {"success": bool, "successMessage": str, "failureMessage": str}}
        """
        results = {}

        try:
            # Check 1: Verify connection
            if self.client:
                conn_ok = await self.client.verify_connection()
                results["connectionCheck"] = {
                    "success": conn_ok,
                    "successMessage": "Successfully connected to data source",
                    "failureMessage": "Failed to connect to data source",
                }
            else:
                results["connectionCheck"] = {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": "Client not initialized",
                }

            # -----------------------------------------------------------------
            # TODO: Add additional preflight checks as needed
            # Example: permissions check, schema validation, etc.
            # -----------------------------------------------------------------

        except Exception as e:
            logger.error(f"Preflight check failed: {e}")
            results["error"] = {
                "success": False,
                "successMessage": "",
                "failureMessage": str(e),
            }

        return results

    @staticmethod
    async def get_configmap(config_map_id: str) -> Dict[str, Any]:
        """
        Return UI configuration JSON.

        Args:
            config_map_id: Either credential config or workflow config ID.

        Returns:
            Configuration dictionary for the UI.
        """
        templates_dir = Path(__file__).parent / "templates"

        if config_map_id == "atlan-connectors-template":
            config_path = templates_dir / "credential.json"
        else:
            config_path = templates_dir / "workflow.json"

        with open(config_path) as f:
            return json.load(f)
