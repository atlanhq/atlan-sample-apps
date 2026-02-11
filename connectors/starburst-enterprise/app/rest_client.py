"""
REST client for Starburst Enterprise (SEP) API.

Handles communication with the SEP REST API to extract:
- Domains
- Data Products (with embedded Datasets and Dataset Columns)
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
            List of domain dictionaries with keys like:
            - id, name, description, schemaLocation, etc.
        """
        client = await self._get_client()
        response = await client.get(f"{DATA_PRODUCT_API_BASE}/domains")
        response.raise_for_status()
        return response.json()

    async def fetch_data_products(self) -> List[Dict[str, Any]]:
        """Fetch all data products from SEP.

        Each data product contains embedded datasets and their columns.

        Returns:
            List of data product dictionaries with keys like:
            - id, name, summary, description, catalogName, schemaName,
              status, dataDomainId, datasets, owners, etc.
        """
        client = await self._get_client()
        response = await client.get(
            f"{DATA_PRODUCT_API_BASE}/products",
            params={"searchOptions": ""},
        )
        response.raise_for_status()
        return response.json()

    async def fetch_data_product_by_id(
        self, product_id: str
    ) -> Dict[str, Any]:
        """Fetch a single data product by its ID.

        Args:
            product_id: The data product identifier.

        Returns:
            Data product dictionary with full details including datasets.
        """
        client = await self._get_client()
        response = await client.get(
            f"{DATA_PRODUCT_API_BASE}/products/{product_id}"
        )
        response.raise_for_status()
        return response.json()
