from application_sdk.clients.models import DatabaseConfig
from application_sdk.clients.sql import AsyncBaseSQLClient


class SQLClient(AsyncBaseSQLClient):
    """
    This client handles connection string generation based on authentication
    type and manages database connectivity using SQLAlchemy.

    """

    DB_CONFIG = DatabaseConfig(
        template="postgresql+psycopg://{username}:{password}@{host}:{port}/{database}",
        required=["username", "password", "host", "port", "database"],
        defaults={
            "connect_timeout": 5,
            "application_name": "Atlan",
        },
        parameters=["sslmode"],  # Allow sslmode to be passed from credentials
        connect_args={
            "sslmode": "prefer",  # Default to prefer SSL, but allow override
        },
    )
