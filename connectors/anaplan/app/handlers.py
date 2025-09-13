from typing import Any, Dict, List

from app.activities.extracts.apps import extract_apps_data
from app.activities.extracts.pages import extract_pages_with_details
from app.clients import AppClient
from application_sdk.handlers.base import BaseHandler
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class AnaplanHandler(BaseHandler):
    """Anaplan App fastAPI handler for UI interactions.

    ------------------------------------------------------------
    CALL CHAIN: Frontend --> SDK --> AnaplanHandler --> Anaplan API --> Response back to frontend
    ENDPOINTS: /workflows/v1/auth, /workflows/v1/metadata, /workflows/v1/check

    SDK BEHAVIOR: Base handler automatically calls load() with credentials before calling any method,
    then wraps responses in standard format ({"success": true/false, "data": ...})

    FUNCTION SIGNATURES:
    - load(credentials: Dict[str, Any]) - SDK passes credentials dict to the parent BaseHandler.load() method which then calls the client.load() method with the credentials
    - test_auth() - No parameters passed after calling load(), uses credentials from load()
    - fetch_metadata(**kwargs) - SDK passes metadata_type and database to the method from the complete payload after calling load(), but ignored for Anaplan
    - preflight_check(payload: Dict[str, Any]) - SDK passes full payload sent to the endpoint to this method after calling load()

    NOTE: For more details on the FastAPI endpoints and their expected requests and responses, check application_sdk/server/fastapi/__init__.py
    """

    def __init__(self, client: AppClient | None = None):
        """Initialize Anaplan handler with optional client instance."""

        super().__init__(client=client)
        self.client: AppClient | None = client

    # ============================================================================
    # SECTION 1: SDK INTERFACE METHODS (Called by FastAPI endpoints)
    # ============================================================================

    async def test_auth(self) -> bool:
        """UI interaction: Test Anaplan authentication credentials.

        ------------------------------------------------------------
        ENDPOINT: POST /workflows/v1/auth (triggered by UI "Test Connection" button)
        SDK BEHAVIOR:
        - Before: Calls load() with credentials from request payload and then calls this method
        - After: Wraps boolean response in {"success": true/false, "message": "..."}
        """
        try:
            if not self.client:
                logger.error("Anaplan client not initialized")
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
        """UI interaction: Fetch Anaplan metadata (apps, pages) for UI filter display.

        ------------------------------------------------------------
        ENDPOINT: POST /workflows/v1/metadata (triggered by UI when user reaches page 3)
        SDK BEHAVIOR:
        - Before: Calls load() with credentials from request payload and then calls this method with metadata_type and database attributes from the request payload if passed, but ignored for Anaplan
        - After: Wraps boolean response in {"success": true/false, "data": "..."} where data is the response from this method

        SAMPLE RESPONSE: [
            {
                "value": "app1",
                "title": "App 1",
                "children": [
                    {
                        "value": "page1",
                        "title": "Page 1",
                        "children": []
                    }
                ]
            }
        ]
        """
        try:
            if not self.client:
                raise Exception("Anaplan client not initialized")

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
                self.client,
                {app[0] for app in active_apps}
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
            raise Exception(f"Failed to fetch metadata: {str(e)}")

    async def preflight_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """UI interaction: Validate Anaplan configuration before workflow execution.

        ------------------------------------------------------------
        ENDPOINT: POST /workflows/v1/check (triggered by UI when user clicks the "Run Preflight Checks" button or clicks the "Start Workflow" button)
        SDK BEHAVIOR:
        - Before: Calls load() with credentials from request payload and then calls this method with the entire payload
        - After: Wraps boolean response in {"success": true/false, "data": "..."} where data is the response from this method

        SAMPLE RESPONSE: {
            "inputValidation": {"success": true, "successMessage": "Input validation passed", "failureMessage": ""},
            "authenticationCheck": {"success": true, "successMessage": "Validated", "failureMessage": ""},
            "appPermissions": {"success": true, "successMessage": "Connected", "failureMessage": ""}
        }

        EXPECTED PAYLOAD STRUCTURE:
        {
          "credentials": {
            "host": "<host>",
            "authType": "basic",
            "username": "<username>",
            "password": "<password>"
          },
          "metadata": {
            "include-metadata": "{\"app1\":{\"page1\":{}}}",
            "exclude-metadata": "{}"
          }
        }
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
