"""
REST client for Starburst Enterprise (SEP) API.

Handles communication with the SEP REST API to extract:
- Domains (with assignedDataProducts)
- Data Products (list returns summary; detail returns views + materializedViews)
- Datasets = views + materializedViews within each Data Product
- Dataset Columns = columns within each view/materializedView

Uses Basic auth for the core REST API and optionally establishes a UI
session (cookie-based) to access supplementary fields like domain/product
type that are only returned by the UI API proxy.
"""

import base64
from typing import Any, Dict, List, Optional

import httpx
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)

# SEP REST API base paths
DATA_PRODUCT_API_BASE = "/api/v1/dataProduct"
UI_DATA_PRODUCT_API_BASE = "/ui/api/v1/dataProduct"


class SEPRestClient:
    """Client for Starburst Enterprise REST API (Data Products, Domains, Datasets)."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        http_scheme: str = "https",
        role: str = "sysadmin",
        verify_ssl: bool = True,
    ):
        self.base_url = f"{http_scheme}://{host}:{port}"
        self.username = username
        self.password = password
        self.role = role
        self.verify_ssl = verify_ssl

        # Build auth header (Basic auth: base64 of username:password)
        credentials = base64.b64encode(
            f"{username}:{password}".encode()
        ).decode()
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {credentials}",
            "X-Trino-Role": f"system=ROLE{{{role}}}",
        }

        self._client: Optional[httpx.AsyncClient] = None
        self._ui_client: Optional[httpx.AsyncClient] = None
        self._ui_session_active = False

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=httpx.Timeout(60.0),
            )
        return self._client

    async def _get_ui_client(self) -> Optional[httpx.AsyncClient]:
        """Get authenticated UI session client for supplementary field access.

        The UI API proxy at /ui/api/v1/dataProduct returns additional fields
        (type, domainName, canEdit) that the raw REST API does not include.
        This method establishes a session via the UI login endpoint.
        """
        if self._ui_client is not None and not self._ui_client.is_closed:
            return self._ui_client

        try:
            self._ui_client = httpx.AsyncClient(
                base_url=self.base_url,
                verify=self.verify_ssl,
                timeout=httpx.Timeout(60.0),
            )
            response = await self._ui_client.post(
                "/ui/api/insights/login",
                json={"username": self.username, "password": self.password},
            )
            if response.status_code == 200:
                self._ui_session_active = True
                logger.info("UI session established for supplementary field access")
                return self._ui_client
            else:
                logger.warning(
                    f"UI login returned status {response.status_code}, "
                    "supplementary fields (type, domainName) may be missing"
                )
                return None
        except Exception as e:
            logger.warning(f"UI session login failed: {e}")
            return None

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        if self._ui_client and not self._ui_client.is_closed:
            await self._ui_client.aclose()

    async def test_connection(self) -> bool:
        """Test connectivity to the SEP REST API."""
        client = await self._get_client()
        response = await client.get(f"{DATA_PRODUCT_API_BASE}/domains")
        response.raise_for_status()
        return True

    async def fetch_domains(self) -> List[Dict[str, Any]]:
        """Fetch all data domains from SEP.

        Uses the UI API session when available to include the ``type`` field
        (PRIVATE/PUBLIC). Falls back to the raw REST API which omits it.

        Returns:
            List of domain dicts. Each contains:
            - id, name, description, schemaLocation (optional),
              assignedDataProducts [{id, name}], type (via UI session),
              createdBy, createdAt, updatedAt, updatedBy
        """
        # Try UI API first for full field coverage
        ui_client = await self._get_ui_client()
        if ui_client:
            try:
                response = await ui_client.get(
                    f"{UI_DATA_PRODUCT_API_BASE}/domains"
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.warning(f"UI API domains fetch failed, falling back: {e}")

        # Fallback to raw API
        client = await self._get_client()
        response = await client.get(f"{DATA_PRODUCT_API_BASE}/domains")
        response.raise_for_status()
        return response.json()

    async def fetch_data_products_summary(self) -> List[Dict[str, Any]]:
        """Fetch all data products (summary only, no datasets).

        Uses the UI API session when available to include supplementary
        fields like domainName, domainType, and type. Falls back to the
        raw REST API.

        Returns:
            List of product summary dicts with:
            - id, name, catalogName, schemaName, dataDomainId, summary,
              description, createdBy, status, timestamps, ratingsCount,
              domainName, type (via UI session)
        """
        # Try UI API first for full field coverage
        ui_client = await self._get_ui_client()
        if ui_client:
            try:
                response = await ui_client.get(
                    f"{UI_DATA_PRODUCT_API_BASE}/products",
                    params={"searchOptions": ""},
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.warning(
                    f"UI API products fetch failed, falling back: {e}"
                )

        # Fallback to raw API
        client = await self._get_client()
        response = await client.get(
            f"{DATA_PRODUCT_API_BASE}/products",
            params={"searchOptions": ""},
        )
        response.raise_for_status()
        return response.json()

    async def fetch_data_product_detail(
        self, product_id: str
    ) -> Dict[str, Any]:
        """Fetch a single data product with full details.

        Uses the UI API session when available for the ``type`` field.
        Falls back to the raw REST API.

        The detail endpoint includes:
        - views[]: Regular view datasets with columns
        - materializedViews[]: Materialized view datasets with columns and refresh schedule
        - owners[]: Owner name/email pairs
        - relevantLinks[], accessMetadata, etc.

        Each view/materializedView contains:
        - name, description, definitionQuery, status, columns[],
          viewSecurityMode, markedForDeletion, timestamps

        Each column contains:
        - name, type, description

        Args:
            product_id: The data product UUID.
        """
        # Try UI API first
        ui_client = await self._get_ui_client()
        if ui_client:
            try:
                response = await ui_client.get(
                    f"{UI_DATA_PRODUCT_API_BASE}/products/{product_id}"
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.warning(
                    f"UI API detail fetch failed for {product_id}, "
                    f"falling back: {e}"
                )

        # Fallback to raw API
        client = await self._get_client()
        response = await client.get(
            f"{DATA_PRODUCT_API_BASE}/products/{product_id}"
        )
        response.raise_for_status()
        return response.json()

    async def fetch_all_data_products_with_details(self) -> List[Dict[str, Any]]:
        """Fetch all data products with full details (views, columns, owners).

        First fetches the summary list to get IDs, then fetches each product's
        detail endpoint to get the embedded views/materializedViews.
        Merges summary-only fields (domainName, lastQueriedAt, etc.) into detail.

        Returns:
            List of fully detailed data product dicts.
        """
        summaries = await self.fetch_data_products_summary()
        detailed_products: List[Dict[str, Any]] = []

        for summary in summaries:
            product_id = summary.get("id")
            if not product_id:
                continue
            try:
                detail = await self.fetch_data_product_detail(product_id)
                # Merge summary-only fields into detail response
                for field in ("domainName", "domainType", "type"):
                    if field in summary and field not in detail:
                        detail[field] = summary[field]
                detailed_products.append(detail)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch detail for data product {product_id} "
                    f"({summary.get('name', 'unknown')}): {e}"
                )
                # Fall back to summary (no views/columns)
                detailed_products.append(summary)

        return detailed_products
