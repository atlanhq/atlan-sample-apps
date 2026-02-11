"""
SQL client for Starburst Enterprise (SEP) via Trino protocol.

Uses the trino Python DBAPI driver directly (sync). The trino package
does not support async SQLAlchemy, so we wrap sync calls with
asyncio.to_thread for non-blocking execution in activities.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

from trino.auth import BasicAuthentication
from trino.dbapi import connect

from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class SEPSQLClient:
    """SQL client for Starburst Enterprise using the Trino DBAPI driver.

    All query methods are async wrappers around sync trino DBAPI calls,
    using asyncio.to_thread to avoid blocking the event loop.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str = "",
        http_scheme: str = "https",
        catalog: str = "system",
        role: str = "sysadmin",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.http_scheme = http_scheme
        self.catalog = catalog
        self.role = role

    def _get_connection(self, catalog: Optional[str] = None):
        """Create a new sync trino DBAPI connection."""
        conn_kwargs: Dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "user": self.username,
            "http_scheme": self.http_scheme,
            "catalog": catalog or self.catalog,
        }
        if self.password:
            conn_kwargs["auth"] = BasicAuthentication(self.username, self.password)
        return connect(**conn_kwargs)

    def _execute_sync(
        self, query: str, catalog: Optional[str] = None
    ) -> Tuple[List[str], List[Any]]:
        """Execute a SQL query synchronously and return (column_names, rows)."""
        conn = self._get_connection(catalog=catalog)
        try:
            cur = conn.cursor()
            cur.execute(query)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            return columns, rows
        finally:
            conn.close()

    async def execute(
        self, query: str, catalog: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a SQL query asynchronously. Returns list of row dicts."""
        columns, rows = await asyncio.to_thread(
            self._execute_sync, query, catalog
        )
        return [dict(zip(columns, row)) for row in rows]

    async def test_connection(self) -> bool:
        """Test SQL connectivity by running SELECT 1."""
        result = await self.execute("SELECT 1")
        return len(result) > 0

    async def fetch_catalogs(self) -> List[Dict[str, Any]]:
        """Fetch all catalogs from system.metadata.catalogs.

        Returns rows with: catalog_name, connector_id, connector_name, state
        """
        return await self.execute(
            "SELECT catalog_name, connector_id, connector_name, state "
            "FROM system.metadata.catalogs "
            "WHERE catalog_name != 'system' "
            "ORDER BY catalog_name"
        )

    async def fetch_schemas(self, catalog: str) -> List[Dict[str, Any]]:
        """Fetch schemas from a specific catalog's information_schema."""
        return await self.execute(
            f"SELECT catalog_name, schema_name "
            f'FROM "{catalog}".information_schema.schemata '
            f"WHERE schema_name != 'information_schema'",
            catalog=catalog,
        )

    async def fetch_tables(self, catalog: str) -> List[Dict[str, Any]]:
        """Fetch tables and views from a specific catalog's information_schema."""
        return await self.execute(
            f"SELECT table_catalog, table_schema, table_name, table_type "
            f'FROM "{catalog}".information_schema.tables '
            f"WHERE table_schema != 'information_schema'",
            catalog=catalog,
        )

    async def fetch_columns(self, catalog: str) -> List[Dict[str, Any]]:
        """Fetch columns from a specific catalog's information_schema.

        Includes the comment field which captures column-level documentation
        set via COMMENT ON COLUMN statements in Trino/SEP.
        """
        return await self.execute(
            f"SELECT table_catalog, table_schema, table_name, column_name, "
            f"ordinal_position, column_default, is_nullable, data_type, comment "
            f'FROM "{catalog}".information_schema.columns '
            f"WHERE table_schema != 'information_schema'",
            catalog=catalog,
        )

    async def fetch_views(self, catalog: str) -> List[Dict[str, Any]]:
        """Fetch view definitions from a specific catalog's information_schema."""
        return await self.execute(
            f"SELECT table_catalog, table_schema, table_name, view_definition "
            f'FROM "{catalog}".information_schema.views '
            f"WHERE table_schema != 'information_schema'",
            catalog=catalog,
        )
