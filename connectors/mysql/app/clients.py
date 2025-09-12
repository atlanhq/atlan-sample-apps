"""
This file contains the client for the SQL metadata extraction application.

Note:
- The DB_CONFIG is overriden from the base class to setup the connection string for the MySQL database.
"""

from application_sdk.clients.sql import AsyncBaseSQLClient


class SQLClient(AsyncBaseSQLClient):
    """
    This client handles connection string generation based on authentication
    type and manages database connectivity using SQLAlchemy.
    """

    DB_CONFIG = {
        "template": "mysql+asyncmy://{user}:{password}@{host}:{port}/{database}",
        "required": ["user", "password", "host", "port", "database"],
    }
