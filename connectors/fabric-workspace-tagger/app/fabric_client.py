"""Microsoft Fabric / Power BI API client for workspace and capacity metadata."""

import re
from typing import Optional

import msal
import requests
from application_sdk.observability.logger_adaptor import get_logger

from app.models import AppConfig, FabricCapacity, FabricWorkspace

logger = get_logger(__name__)


class FabricAPIClient:
    """Client for Microsoft Fabric and Power BI Admin APIs."""

    POWER_BI_ADMIN_BASE_URL = "https://api.powerbi.com/v1.0/myorg/admin"
    FABRIC_ADMIN_BASE_URL = "https://api.fabric.microsoft.com/v1/admin"

    def __init__(self, config: AppConfig, client_secret: str):
        """Initialize Fabric API client with configuration.

        Args:
            config: Application configuration
            client_secret: Azure AD client secret for service principal auth
        """
        self.config = config
        self.client_secret = client_secret
        self._access_token: Optional[str] = None

    def _get_access_token(self) -> str:
        """Obtain Azure AD access token using client credentials flow.

        Returns:
            Bearer access token

        Raises:
            Exception: If token acquisition fails
        """
        if self._access_token:
            return self._access_token

        logger.info(
            f"Acquiring access token for tenant {self.config.fabric_tenant_id}"
        )

        authority = f"{self.config.fabric_authority_url}/{self.config.fabric_tenant_id}"
        app = msal.ConfidentialClientApplication(
            client_id=self.config.fabric_client_id,
            client_credential=self.client_secret,
            authority=authority,
        )

        result = app.acquire_token_for_client(scopes=[self.config.fabric_scope])

        if "access_token" in result:
            self._access_token = result["access_token"]
            logger.info("Successfully acquired access token")
            return self._access_token
        else:
            error_msg = result.get("error_description", result.get("error", "Unknown error"))
            logger.error(f"Failed to acquire token: {error_msg}")
            raise Exception(f"Token acquisition failed: {error_msg}")

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
    ) -> dict:
        """Make authenticated HTTP request to Fabric/Power BI API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            params: Query parameters
            json_body: JSON request body

        Returns:
            Response JSON

        Raises:
            requests.HTTPError: If request fails
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            timeout=60,
        )

        response.raise_for_status()
        return response.json()

    def list_capacities(self) -> list[FabricCapacity]:
        """List all Power BI / Fabric capacities.

        Returns:
            List of capacity models
        """
        logger.info("Fetching Power BI capacities")
        url = f"{self.POWER_BI_ADMIN_BASE_URL}/capacities"

        try:
            response = self._make_request("GET", url)
            capacities = response.get("value", [])

            logger.info(f"Fetched {len(capacities)} capacities")

            return [
                FabricCapacity(
                    id=cap["id"],
                    display_name=cap.get("displayName", cap.get("name", cap["id"])),
                    sku=cap.get("sku"),
                    region=cap.get("region"),
                    state=cap.get("state"),
                )
                for cap in capacities
            ]
        except Exception as e:
            logger.error(f"Failed to fetch capacities: {e}", exc_info=True)
            return []

    def list_workspaces(self) -> list[FabricWorkspace]:
        """List all Power BI workspaces (groups) with capacity info.

        Returns:
            List of workspace models
        """
        logger.info("Fetching Power BI workspaces")
        url = f"{self.POWER_BI_ADMIN_BASE_URL}/groups"

        try:
            # Fetch workspaces with expand=users to get additional metadata
            # Note: We use $top to paginate if needed
            response = self._make_request("GET", url, params={"$top": 5000})
            workspaces_raw = response.get("value", [])

            logger.info(f"Fetched {len(workspaces_raw)} raw workspaces")

            # Build capacity lookup
            capacities = self.list_capacities()
            capacity_map = {cap.id: cap for cap in capacities}

            # Filter and normalize workspaces
            workspaces = []
            filter_regex = (
                re.compile(self.config.workspace_filter_regex)
                if self.config.workspace_filter_regex
                else None
            )

            for ws in workspaces_raw:
                ws_id = ws.get("id")
                ws_name = ws.get("name", "")

                # Apply optional regex filter
                if filter_regex and not filter_regex.search(ws_name):
                    continue

                capacity_id = ws.get("capacityId")
                capacity = capacity_map.get(capacity_id) if capacity_id else None

                # Extract custom tags from workspace metadata
                # Note: Power BI API doesn't have a native "tags" field;
                # you might derive tags from naming conventions, descriptions,
                # or custom metadata fields. This is a placeholder.
                tags = self._extract_tags_from_workspace(ws)

                workspaces.append(
                    FabricWorkspace(
                        id=ws_id,
                        name=ws_name,
                        capacity_id=capacity_id,
                        capacity_name=capacity.display_name if capacity else None,
                        tags=tags,
                        state=ws.get("state", "Active"),
                    )
                )

            logger.info(f"Normalized {len(workspaces)} workspaces after filtering")
            return workspaces

        except Exception as e:
            logger.error(f"Failed to fetch workspaces: {e}", exc_info=True)
            raise

    def _extract_tags_from_workspace(self, workspace: dict) -> dict[str, str]:
        """Extract custom tags from workspace metadata.

        Since Power BI API doesn't have native tags, this method uses
        naming conventions or description parsing as a heuristic.

        For example, a workspace named "Manufacturing - Critical - Prod"
        might yield tags: {"pillar": "Manufacturing", "env": "prod"}.

        Override this logic based on your organization's conventions.

        Args:
            workspace: Raw workspace dict from Power BI API

        Returns:
            Dictionary of tag key-value pairs
        """
        tags = {}

        # Example heuristic: parse workspace name for patterns
        name = workspace.get("name", "")

        # Example: Extract "Manufacturing" from "Manufacturing BI" → pillar:Manufacturing
        # You can customize this logic based on your naming conventions
        if "Manufacturing" in name:
            tags["pillar"] = "Manufacturing"
        elif "Sales" in name:
            tags["pillar"] = "Sales"
        elif "Finance" in name:
            tags["pillar"] = "Finance"

        # Example: Extract environment from name
        if "Prod" in name or "Production" in name:
            tags["env"] = "prod"
        elif "Dev" in name or "Development" in name:
            tags["env"] = "dev"

        # You could also parse description field if available
        description = workspace.get("description", "")
        if description:
            # Add custom parsing logic here
            pass

        return tags
