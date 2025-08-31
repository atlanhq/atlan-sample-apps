import json
from typing import Any, Dict, List, Set

from application_sdk.handlers.base import BaseHandler
from application_sdk.observability.logger_adaptor import get_logger

from app.clients import AnaplanApiClient

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

    def __init__(self, client: AnaplanApiClient | None = None):
        """Initialize Anaplan handler with optional client instance."""

        super().__init__(client=client)
        self.client: AnaplanApiClient | None = client

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
            apps = await self._extract_apps_for_handler()
            if not apps:
                logger.warning("No apps found")
                return []  # Return empty list, SDK will wrap it

            # Build hierarchical response
            metadata_items = []
            active_apps = []

            # Process apps and create app items (filter out deleted apps)
            for app in apps:
                if app.get("deletedAt") is None:  # Only include non-deleted apps
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
            all_pages = await self._extract_pages_for_handler({app[0] for app in active_apps})
            
            # Group pages by app GUID
            app_pages_mapping = {}
            for page in all_pages:
                if page.get("deletedAt") is not None:  # Skip deleted pages
                    continue
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

            # Check 1: Input Validation
            results["inputValidation"] = AnaplanHandler._validate_input_payload(payload)

            # Check 2: Authentication Check
            results[
                "authenticationCheck"
            ] = await AnaplanHandler._validate_authentication(self.client)

            # Check 3: App Permissions Check
            results["appPermissions"] = await AnaplanHandler._validate_app_permissions(self.client)

            return results

        except Exception as e:
            logger.error(f"Preflight check failed: {str(e)}")
            return {
                "inputValidation": {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": f"Preflight check failed: {str(e)}",
                }
            }

    # ============================================================================
    # SECTION 2: VALIDATION METHODS (Static helpers for preflight checks)
    # ============================================================================

    @staticmethod
    def _validate_input_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the structure and content of the input payload"""
        try:
            # Check for required top-level keys
            required_keys = ["credentials", "metadata"]
            missing_keys = [key for key in required_keys if key not in payload]

            if missing_keys:
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": f"Missing required keys in the payload: {', '.join(missing_keys)}",
                }

            # Validate credentials structure
            credentials = payload.get("credentials", {})
            if not isinstance(credentials, dict):
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": "Credentials must be a dictionary",
                }

            # Check for required credential fields
            required_credential_keys = ["host", "authType", "username", "password"]
            missing_credential_keys = [
                key for key in required_credential_keys if key not in credentials
            ]

            if missing_credential_keys:
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": f"Missing credential fields: {', '.join(missing_credential_keys)}",
                }

            # Validate metadata structure
            metadata = payload.get("metadata", {})
            if not isinstance(metadata, dict):
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": "Metadata must be a dictionary",
                }

            # Check for required metadata fields
            required_metadata_keys = [
                "include-metadata",
                "exclude-metadata",
            ]
            missing_metadata_keys = [
                key for key in required_metadata_keys if key not in metadata
            ]

            if missing_metadata_keys:
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": f"Missing metadata fields: {', '.join(missing_metadata_keys)}",
                }

            # Validate that metadata values are JSON strings
            try:
                json.loads(metadata.get("include-metadata", "{}"))
                json.loads(metadata.get("exclude-metadata", "{}"))
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": f"Invalid JSON in metadata: {str(e)}",
                }

            # All validations passed
            return {
                "success": True,
                "successMessage": "Input Validation Successful",
                "failureMessage": "",
            }

        except Exception as e:
            logger.error(f"Input validation failed: {str(e)}")
            return {
                "success": False,
                "successMessage": "",
                "failureMessage": f"Input validation error: {str(e)}",
            }

    @staticmethod
    async def _validate_authentication(anaplan_client: AnaplanApiClient | None
    ) -> Dict[str, Any]:
        """Validate authentication credentials"""
        try:
            if not anaplan_client:
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": "Anaplan client not initialized",
                }

            # Test authentication by calling _get_auth_token
            try:
                # Run the async authentication test (no event loop needed since we're already async)
                auth_result = await anaplan_client._get_auth_token()

                if auth_result:
                    return {
                        "success": True,
                        "successMessage": "Authentication successful - token generated",
                        "failureMessage": "",
                    }
                else:
                    return {
                        "success": False,
                        "successMessage": "",
                        "failureMessage": "Authentication failed - could not generate token",
                    }

            except Exception as auth_error:
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": f"Authentication error: {str(auth_error)}",
                }

        except Exception as e:
            return {
                "success": False,
                "successMessage": "",
                "failureMessage": f"Authentication validation error: {str(e)}",
            }

    @staticmethod
    async def _validate_app_permissions(anaplan_client: AnaplanApiClient | None) -> Dict[str, Any]:
        """Validate app permissions"""
        try:
            if not anaplan_client:
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": "Anaplan client not initialized",
                }

            # Test host connectivity by calling app assets endpoint
            try:
                # First ensure we have a valid auth token
                auth_result = await anaplan_client._get_auth_token()
                if not auth_result:
                    return {
                        "success": False,
                        "successMessage": "",
                        "failureMessage": "Authentication failed - cannot validate host without valid token",
                    }

                # Test host by calling the app assets endpoint (first page only)
                host = anaplan_client.host
                url = f"https://{host}/a/springboard-definition-service/apps"
                params = {"limit": 1, "offset": 0}  # Just get first page with 1 item

                response = await anaplan_client.execute_http_get_request(
                    url=url, params=params
                )

                if response is None:
                    return {
                        "success": False,
                        "successMessage": "",
                        "failureMessage": f"App permissions validation failed - no response from {host}",
                    }

                if response.status_code == 200:
                    # Try to parse the response to ensure it's valid JSON
                    try:
                        response_dict = response.json()
                        # Check if response has expected structure
                        if "items" in response_dict:
                            return {
                                "success": True,
                                "successMessage": f"App permissions validation successful - connected to {host}",
                                "failureMessage": "",
                            }
                        else:
                            return {
                                "success": False,
                                "successMessage": "",
                                "failureMessage": f"App permissions validation failed - unexpected response format from {host}",
                            }
                    except Exception as json_error:
                        return {
                            "success": False,
                            "successMessage": "",
                            "failureMessage": f"App permissions validation failed - invalid JSON response from {host}: {str(json_error)}",
                        }
                else:
                    return {
                        "success": False,
                        "successMessage": "",
                        "failureMessage": f"App permissions validation failed - HTTP {response.status_code} from {host}",
                    }

            except Exception as host_error:
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": f"App permissions validation error: {str(host_error)}",
                }

        except Exception as e:
            return {
                "success": False,
                "successMessage": "",
                "failureMessage": f"App permissions validation error: {str(e)}",
            }

    # ============================================================================
    # SECTION 3: METADATA METHODS (Static helpers for fetch metadata)
    # ============================================================================

    async def _extract_apps_for_handler(self) -> List[Dict[str, Any]]:
        """Extract apps data for handler"""
        try:
            logger.info("Starting apps data extraction for handler from Anaplan API")

            # app data dict
            app_data: List[Dict[str, Any]] = []

            # Extract app assets from Anaplan with pagination
            url = f"https://{self.client.host}/a/springboard-definition-service/apps"
            limit = 100
            offset = 0

            # Paginate through all apps and collect directly in app_data
            while True:
                params = {"limit": limit, "offset": offset}

                response = await self.client.execute_http_get_request(url, params=params)

                if response is None:
                    logger.error("Failed to extract apps data: No response received")
                    raise ValueError("Failed to extract apps data: No response received")

                if not response.is_success:
                    raise ValueError(f"Failed to fetch apps: {response.status_code}")

                response_dict = response.json()
                app_data.extend(response_dict.get("items", []))

                paging = response_dict.get("paging", {})
                total_size = paging.get("totalItemCount", 0)
                offset += limit

                if offset >= total_size:
                    break

            # Filter out deleted apps only (no other filters applied)
            filtered_app_data = [app for app in app_data if app.get("deletedAt") is None]

            logger.info(
                f"Successfully extracted {len(filtered_app_data)} non-deleted apps from {len(app_data)} total apps for handler"
            )
            return filtered_app_data

        except Exception as e:
            logger.error(f"Error extracting apps data for handler: {str(e)}")
            raise

    async def _extract_pages_for_handler(self, app_guids: Set[str]) -> List[Dict[str, Any]]:
        """Extract pages data for handler
        
        Args:
            app_guids: Set of app GUIDs to filter pages by
        """
        try:
            logger.info("Starting pages data extraction for handler from Anaplan API")

            # page data dict
            page_data: List[Dict[str, Any]] = []

            # Extract page assets from Anaplan with pagination
            url = f"https://{self.client.host}/a/springboard-definition-service/pages"
            limit = 100
            offset = 0

            # Paginate through all pages and collect directly in page_data
            while True:
                params = {
                    "limit": limit,
                    "offset": offset,
                    "sort": "lastAccessed",
                    "order": "desc",
                    "includeReportPages": True,
                }

                response = await self.client.execute_http_get_request(url, params=params)

                if response is None:
                    logger.error("Failed to extract pages data: No response received")
                    raise ValueError("Failed to extract pages data: No response received")

                if not response.is_success:
                    raise ValueError(f"Failed to fetch pages: {response.status_code}")

                response_dict = response.json()
                items = response_dict.get("items", [])
                
                if not items:
                    break  # No more pages to fetch

                page_data.extend(items)
                offset += limit

            # Filter out deleted, archived pages, and pages with invalid app GUIDs
            valid_pages = [
                page
                for page in page_data
                if page.get("deletedAt") is None
                and not page.get("isArchived", False)
                and page.get("appGuid") in app_guids
            ]

            logger.info(
                f"Successfully extracted {len(valid_pages)} valid pages from {len(page_data)} total pages for handler"
            )
            return valid_pages

        except Exception as e:
            logger.error(f"Error extracting pages data for handler: {str(e)}")
            raise
