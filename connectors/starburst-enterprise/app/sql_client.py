"""
SQL client for Starburst Enterprise (SEP) via Trino protocol.

Uses the trino Python driver with SQLAlchemy to query INFORMATION_SCHEMA
for catalogs, schemas, tables, views, and columns.
"""

from application_sdk.clients.models import DatabaseConfig
from application_sdk.clients.sql import AsyncBaseSQLClient


class SEPSQLClient(AsyncBaseSQLClient):
    """SQL client for Starburst Enterprise using the Trino SQLAlchemy dialect.

    Connection string format:
        trino://{user}:{password}@{host}:{port}/{catalog}

    The trino SQLAlchemy driver handles Basic/LDAP auth via the password parameter.
    """

    DB_CONFIG = DatabaseConfig(
        template="trino://{user}:{password}@{host}:{port}/{catalog}",
        required=["user", "host", "port"],
        defaults={
            "port": "8080",
            "catalog": "system",
        },
    )
