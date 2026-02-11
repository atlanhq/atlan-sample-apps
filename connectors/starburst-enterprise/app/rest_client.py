"""
REST client for Starburst Enterprise (SEP) API.

Handles communication with the SEP REST API to extract:
- Domains (with assignedDataProducts)
- Data Products (list returns summary; detail returns views + materializedViews)
- Datasets = views + materializedViews within each Data Product
- Dataset Columns = columns within each view/materializedView
"""

import base64
from typing import Any, Dict, List, Optional

import httpx
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)

# SEP REST API base path
DATA_PRODUCT_API_BASE = "/api/v1/dataProduct"


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

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=httpx.Timeout(60.0),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def test_connection(self) -> bool:
        """Test connectivity to the SEP REST API."""
        client = await self._get_client()
        response = await client.get(f"{DATA_PRODUCT_API_BASE}/domains")
        response.raise_for_status()
        return True

    async def fetch_domains(self) -> List[Dict[str, Any]]:
        """Fetch all data domains from SEP.

        Returns:
            List of domain dicts. Each contains:
            - id, name, description, schemaLocation (optional),
              assignedDataProducts [{id, name}],
              createdBy, createdAt, updatedAt, updatedBy
        """
        client = await self._get_client()
        response = await client.get(f"{DATA_PRODUCT_API_BASE}/domains")
        response.raise_for_status()
        return response.json()

    async def fetch_data_products_summary(self) -> List[Dict[str, Any]]:
        """Fetch all data products (summary only, no datasets).

        The list endpoint returns product metadata but NOT the embedded
        views/materializedViews. Use fetch_data_product_detail() for those.

        Returns:
            List of product summary dicts with:
            - id, name, catalogName, schemaName, dataDomainId, summary,
              description, createdBy, status, timestamps, ratingsCount
        """
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
                detailed_products.append(detail)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch detail for data product {product_id} "
                    f"({summary.get('name', 'unknown')}): {e}"
                )
                # Fall back to summary (no views/columns)
                detailed_products.append(summary)

        return detailed_products
