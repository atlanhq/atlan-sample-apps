import json
from pathlib import Path
from typing import Any, Dict, List

from app.clients import AppClient
from app.extracts.apps import extract_apps_data
from app.extracts.pages import extract_pages_with_details
from application_sdk.common.error_codes import ClientError
from application_sdk.handlers.base import BaseHandler
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class AppHandler(BaseHandler):
    """FastAPI handler for UI interactions.

    Handles authentication, metadata fetching, and preflight checks for the App
    connector. Provides endpoints for the 3-page wizard interface.

    Endpoints:
        /workflows/v1/auth: Test authentication credentials
        /workflows/v1/metadata: Fetch available apps and pages
        /workflows/v1/check: Run preflight validation checks

    Note:
        The SDK automatically calls load() with credentials before calling any method
        and wraps responses in standard format ({"success": true/false, "data": ...}).
    """

    def __init__(self, client: AppClient | None = None):
        """Initialize App handler with optional client instance.

        Args:
            client: Optional AppClient instance for API operations.
        """

        super().__init__(client=client)
        self.client: AppClient | None = client

    # ============================================================================
    # SECTION 1: SDK HANDLER METHODS (Called by FastAPI endpoints)
    # ============================================================================

    async def test_auth(self) -> bool:
        """Test App authentication credentials.

        Validates the provided credentials by attempting to obtain an authentication
        token from App's authentication service.

        Returns:
            bool: True if authentication is successful, False otherwise.

        Note:
            Endpoint: POST /workflows/v1/auth (triggered by UI "Test Connection" button)
            The SDK wraps the boolean response in {"success": true/false, "message": "..."}.
        """
        try:
            if not self.client:
                logger.error("App client not initialized")
                return False

            result = await self.client._get_auth_token()
            if result:
                logger.info("Authentication test successful")
                return True
            else:
                logger.error("Authentication test failed")
                return False

        except Exception as exc:
            logger.error(f"Failed to authenticate: {str(exc)}")
            return False

    async def fetch_metadata(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Fetch App metadata (apps, pages) for UI filter display.

        Retrieves all available apps and their associated pages from Anaplan
        and formats them in a hierarchical structure for the UI dropdowns.

        Args:
            **kwargs: Additional keyword arguments (metadata_type and database
                are ignored for App).

        Returns:
            List[Dict[str, Any]]: Hierarchical metadata structure with apps and pages.

        Raises:
            Exception: If client is not initialized or metadata fetching fails.

        Note:
            Endpoint: POST /workflows/v1/metadata (triggered by UI when user reaches page 3)
            The SDK wraps the response in {"success": true/false, "data": "..."}.
        """
        try:
            if not self.client:
                raise ClientError("App client not initialized")

            # Step 1: Ensure we have a valid authentication token
            logger.info("Ensuring authentication token is valid...")
            await self.client._get_auth_token()

            # Step 2: Get all apps and build app items
            logger.info("Fetching all apps...")
            apps = await extract_apps_data(self.client)
            if not apps:
                logger.warning("No apps found")
                return []  # Return empty list, SDK will wrap it

            # Build hierarchical response
            metadata_items = []
            active_apps = []

            # Process apps and create app items (filter out deleted apps)
            for app in apps:
                app_guid = app["guid"]
                app_name = app["name"]

                # Create app item with empty children
                app_item = {
                    "value": app_guid,
                    "title": app_name,
                    "children": [],
                }
                metadata_items.append(app_item)
                active_apps.append((app_guid, app_name))

            # Step 3: Get all pages for all apps concurrently
            logger.info("Fetching pages for all apps...")

            # Get all pages for the active apps
            all_pages = await extract_pages_with_details(
                self.client, {app[0] for app in active_apps}
            )

            # Group pages by app GUID
            app_pages_mapping = {}
            for page in all_pages:
                app_guid = page.get("appGuid")
                if app_guid and app_guid in {app[0] for app in active_apps}:
                    if app_guid not in app_pages_mapping:
                        app_pages_mapping[app_guid] = []
                    app_pages_mapping[app_guid].append(page)

            # Add page items to app children
            for app_guid, app_name in active_apps:
                pages_for_app = app_pages_mapping.get(app_guid, [])

                # Find the app item and add pages to its children
                for app_item in metadata_items:
                    if app_item["value"] == app_guid:
                        for page in pages_for_app:
                            page_item = {
                                "value": page["guid"],
                                "title": page["name"],
                                "children": [],
                            }
                            app_item["children"].append(page_item)
                        break

            return metadata_items  # Return list of nested metadata items

        except Exception as e:
            logger.error(f"Failed to fetch metadata: {str(e)}")
            # For errors, we should raise an exception rather than return a list
            # The SDK will handle the exception and return appropriate error response
            raise ClientError(f"Failed to fetch metadata: {str(e)}")

    async def preflight_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate App configuration before workflow execution.

        Performs authentication and permissions checks to ensure the configuration
        is valid before starting the workflow.

        Args:
            payload: Dictionary containing credentials and metadata configuration.

        Returns:
            Dict[str, Any]: Dictionary with check results for each validation step.

        Note:
            Endpoint: POST /workflows/v1/check (triggered by UI preflight or start workflow)
            The SDK wraps the response in {"success": true/false, "data": "..."}.
        """
        try:
            # Initialize results dictionary
            results = {}

            # Check 1: Authentication Check
            if not self.client:
                results["authenticationCheck"] = {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": "App client not initialized",
                }
            else:
                auth_result = await self.client._get_auth_token()
                if auth_result:
                    results["authenticationCheck"] = {
                        "success": True,
                        "successMessage": "Authentication successful - token generated",
                        "failureMessage": "",
                    }
                else:
                    results["authenticationCheck"] = {
                        "success": False,
                        "successMessage": "",
                        "failureMessage": "Authentication failed - could not generate token",
                    }

            # Check 2: App Permissions Check
            app_data = await extract_apps_data(self.client)

            if app_data:
                results["appPermissions"] = {
                    "success": True,
                    "successMessage": f"App permissions validation successful - connected to {self.client.host}",
                    "failureMessage": "",
                }
            else:
                results["appPermissions"] = {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": "App permissions validation failed - no apps found",
                }

            return results

        except Exception as e:
            logger.error(f"Preflight check failed: {str(e)}")
            return {
                "Exception": {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": f"Preflight check failed: {str(e)}",
                }
            }

    @staticmethod
    async def get_configmap(config_map_id: str) -> Dict[str, Any]:
        workflow_json_path = Path().cwd() / "app" / "templates" / "workflow.json"
        credential_json_path = (
            Path().cwd() / "app" / "templates" / "atlan-connectors-anaplan.json"
        )

        if config_map_id == "atlan-connectors-anaplan":
            with open(credential_json_path) as f:
                return json.load(f)

        with open(workflow_json_path) as f:
            return json.load(f)
