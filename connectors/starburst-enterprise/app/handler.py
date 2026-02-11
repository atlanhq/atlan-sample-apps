"""
Handler for Starburst Enterprise (SEP) connector.

This is a hybrid handler that uses:
- REST client for Data Products, Domains, Datasets, and Dataset Columns
- SQL client (trino DBAPI) for Catalogs, Schemas, Tables, Views, and Table/View Columns

Both clients share the same SEP credentials (Basic/LDAP auth).
"""

from typing import Any, Dict, List, Optional

from app.rest_client import SEPRestClient
from app.sql_client import SEPSQLClient
from application_sdk.handlers.base import BaseHandler
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class SEPHandler(BaseHandler):
    """Hybrid handler for Starburst Enterprise metadata extraction.

    Manages both REST and SQL clients against the same SEP instance.
    The client param is accepted for BaseApplication compatibility but not
    used; this hybrid handler creates its own REST + SQL clients in load().
    """

    def __init__(self, client: Any = None) -> None:
        super().__init__(client=client)
        self.rest_client: Optional[SEPRestClient] = None
        self.sql_client: Optional[SEPSQLClient] = None
        self._credentials: Dict[str, Any] = {}

    async def load(self, credentials: Dict[str, Any]) -> None:
        """Initialize both REST and SQL clients from credentials.

        Expected credential keys:
            host, port, username, password, http_scheme (optional),
            catalog (optional), role (optional)
        """
        self._credentials = credentials

        host = credentials["host"]
        port = int(credentials.get("port", 443))
        username = credentials["username"]
        password = credentials.get("password", "")
        http_scheme = credentials.get("http_scheme", "https")
        role = credentials.get("role", "sysadmin")
        catalog = credentials.get("catalog", "system")

        # Initialize REST client
        self.rest_client = SEPRestClient(
            host=host,
            port=port,
            username=username,
            password=password,
            http_scheme=http_scheme,
            role=role,
        )

        # Initialize SQL client (trino DBAPI - sync wrapped as async)
        self.sql_client = SEPSQLClient(
            host=host,
            port=port,
            username=username,
            password=password,
            http_scheme=http_scheme,
            catalog=catalog,
            role=role,
        )

        logger.info(
            "SEP handler loaded with REST + SQL clients",
            extra={"host": host, "port": port, "catalog": catalog},
        )

    async def test_auth(self, credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Test authentication against both REST API and SQL endpoints."""
        creds = credentials or self._credentials
        if not self.rest_client or not self.sql_client:
            await self.load(creds)

        results: Dict[str, Any] = {}

        # Test REST API
        try:
            await self.rest_client.test_connection()
            results["rest_api"] = {"success": True, "message": "REST API connection successful"}
        except Exception as e:
            results["rest_api"] = {"success": False, "message": f"REST API connection failed: {e}"}

        # Test SQL via trino DBAPI
        try:
            await self.sql_client.test_connection()
            results["sql"] = {"success": True, "message": "SQL connection successful"}
        except Exception as e:
            results["sql"] = {"success": False, "message": f"SQL connection failed: {e}"}

        all_success = all(r.get("success", False) for r in results.values())
        return {"success": all_success, "data": results}

    async def preflight_check(
        self,
        credentials: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate connectivity and access to the requested resources."""
        creds = credentials or self._credentials
        if not self.rest_client or not self.sql_client:
            await self.load(creds)

        checks: Dict[str, Any] = {}

        # Check REST API - can we list domains?
        try:
            domains = await self.rest_client.fetch_domains()
            checks["domainsCheck"] = {
                "success": True,
                "successMessage": f"Domains check successful. Found {len(domains)} domain(s).",
                "failureMessage": "",
            }
        except Exception as e:
            checks["domainsCheck"] = {
                "success": False,
                "successMessage": "",
                "failureMessage": f"Failed to fetch domains: {e}",
            }

        # Check SQL - can we list catalogs?
        try:
            catalogs = await self.sql_client.fetch_catalogs()
            checks["catalogsCheck"] = {
                "success": True,
                "successMessage": f"Catalogs check successful. Found {len(catalogs)} catalog(s).",
                "failureMessage": "",
            }
        except Exception as e:
            checks["catalogsCheck"] = {
                "success": False,
                "successMessage": "",
                "failureMessage": f"Failed to list catalogs: {e}",
            }

        all_success = all(c.get("success", False) for c in checks.values())
        return {"success": all_success, "data": checks}

    async def fetch_metadata(
        self,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fetch high-level metadata for the connection setup UI.

        Returns catalog and schema names for filtering.
        """
        creds = credentials or self._credentials
        if not self.rest_client or not self.sql_client:
            await self.load(creds)

        metadata_items: List[Dict[str, str]] = []

        try:
            catalogs = await self.sql_client.fetch_catalogs()
            for cat in catalogs:
                catalog_name = cat["catalog_name"]
                # Skip internal catalogs
                if catalog_name in ("system", "jmx"):
                    continue
                try:
                    schemas = await self.sql_client.fetch_schemas(catalog_name)
                    for schema in schemas:
                        metadata_items.append({
                            "catalog_name": catalog_name,
                            "schema_name": schema["schema_name"],
                        })
                except Exception:
                    logger.warning(f"Could not list schemas for catalog: {catalog_name}")
        except Exception as e:
            logger.error(f"Failed to fetch metadata: {e}")
            return {"success": False, "data": [], "error": str(e)}

        return {"success": True, "data": metadata_items}

    async def close(self) -> None:
        """Clean up client resources."""
        if self.rest_client:
            await self.rest_client.close()
