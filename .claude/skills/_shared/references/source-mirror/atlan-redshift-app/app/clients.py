import os
import socket
from typing import Any, Dict, Optional
from urllib.parse import quote_plus

import boto3
import sqlalchemy
from application_sdk.clients.models import DatabaseConfig
from application_sdk.clients.sql import BaseSQLClient
from application_sdk.common.aws_utils import (
    create_aws_client,
    create_aws_session,
    create_engine_url,
    get_all_aws_regions,
    get_cluster_credentials,
    get_region_name_from_hostname,
)
from application_sdk.common.utils import parse_credentials_extra
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class RedshiftClient(BaseSQLClient):
    """
    This client handles connection string generation for Redshift based on authentication
    type and manages database connectivity using SQLAlchemy.
    """

    DB_CONFIG: Optional[DatabaseConfig] = DatabaseConfig(
        template="redshift+psycopg2://{username}:{password}@{host}:{port}/{database}",
        required=["host", "port", "database", "username", "password"],
        defaults={
            "connect_timeout": 5,
            "application_name": "Atlan",
        },
        connect_args={"sslmode": "prefer", "connect_timeout": 30},
    )

    def __init__(self, **kwargs):
        """
        Initialize RedshiftClient with Redshift-specific connection arguments.
        """

        if str(os.getenv("ATLAN_ENABLE_REDSHIFT_MINER", "true")).lower() == "true":
            use_server_side_cursor = False
        else:
            use_server_side_cursor = True

        # Call parent __init__ with the Redshift-specific connect args
        super().__init__(
            use_server_side_cursor=use_server_side_cursor,
            **kwargs,
        )

    @property
    def sql_alchemy_connect_args(self) -> Dict[str, Any]:
        """
        Get SQLAlchemy connection arguments for Redshift.

        Returns:
            Dict[str, Any]: Connection arguments including SSL mode.
        """
        assert self.DB_CONFIG is not None, "DB_CONFIG should not be None"
        return self.DB_CONFIG.connect_args or {}

    def _setup_iam_connection(
        self, credentials: Dict[str, Any], extra: Dict[str, Any]
    ) -> None:
        """
        Set up Redshift connection using IAM authentication.

        Args:
            credentials: Dictionary containing connection credentials
        """
        # Create AWS session
        session = create_aws_session(credentials)

        # Extract region from host
        host = credentials["host"]
        region = get_region_name_from_hostname(host)
        if not region:
            raise ValueError(f"Could not extract region from host: {host}")

        # Create Redshift client
        aws_client = create_aws_client(
            service="redshift", region=region, session=session
        )

        # Get cluster credentials
        cluster_credentials = get_cluster_credentials(aws_client, credentials, extra)

        # Create engine URL and establish connection
        engine_url = create_engine_url(
            "redshift+psycopg2", credentials, cluster_credentials, extra
        )

        assert self.DB_CONFIG is not None, "DB_CONFIG should not be None"
        self.engine = sqlalchemy.create_engine(
            str(engine_url), connect_args=self.DB_CONFIG.connect_args or {}
        )

        with self.engine.connect() as _:  # type: ignore
            pass

    async def load(self, credentials: Dict[str, Any]) -> None:
        """
        Generate a SQLAlchemy connection string for Redshift, supporting IAM authentication.

        Args:
            credentials: Dictionary containing connection credentials
        """
        self.credentials = credentials
        extra = parse_credentials_extra(credentials)
        auth_type = credentials.get("authType", "basic").lower()

        if auth_type == "iam" or auth_type == "iam_user":
            self._setup_iam_connection(credentials, extra)

        elif auth_type == "role" or auth_type == "iam_role":
            # --- Config ---
            cluster_id = extra.get("cluster_id", None)
            deployment_type = extra.get("deployment_type", None)
            workgroup = extra.get("workgroup", None)
            database = extra["database"]
            db_user = extra["dbuser"]  # Redshift database user (not IAM user)
            region = extra.get("region_name", None)
            host = credentials["host"]
            port = credentials.get("port", 5439)
            role_arn = extra["aws_role_arn"]
            external_id = extra.get("aws_external_id")  # External ID may be optional

            if region is None or region == "":
                region = get_region_name_from_hostname(credentials["host"])

            if region is None or region == "":
                logger.info(
                    "private link enabled host detected, switching to finding the region "
                )

                filtered_hostname = socket.getfqdn(credentials["host"])
                extracted_region = get_region_name_from_hostname(filtered_hostname)
                logger.info(
                    f"NATIVE : region extracted from private link enabled host: {extracted_region} and filtered_hostname is {filtered_hostname}"
                )

            AWS_REGIONS = get_all_aws_regions()

            # --- Step 1: Assume the IAM Role ---
            assumed_role = None
            if region:
                AWS_REGIONS.remove(region)
                AWS_REGIONS.insert(0, region)
            for region_arn in AWS_REGIONS:
                try:
                    logger.info(f"Assuming role in region {region_arn}")
                    sts_client = boto3.client("sts", region_name=region_arn)

                    assume_role_kwargs = {
                        "RoleArn": role_arn,
                        "RoleSessionName": "atlan_jdbc_metadata_extractor",
                        "DurationSeconds": 3600,
                    }

                    if external_id:
                        assume_role_kwargs["ExternalId"] = external_id

                    assumed_role = sts_client.assume_role(**assume_role_kwargs)
                    logger.info(f"Successfully assumed role in region {region_arn}")
                    break
                except Exception as e:
                    logger.info(
                        f"Error assuming role in region {region_arn}. Trying with other regions: {e}"
                    )
                    continue

            if assumed_role is None:
                raise ValueError("Failed to assume role in any region")

            temp_credentials = assumed_role["Credentials"]
            # --- Step 2: Use the assumed credentials to get Redshift cluster credentials ---
            redshift = create_aws_client(
                service="redshift", region=region, temp_credentials=temp_credentials
            )

            if deployment_type == "serverless" and workgroup:
                # if serverless and workgroup is provided, use workgroup
                logger.info(f"workgroup is provided, using workgroup: {workgroup}")

                redshift_serverless = create_aws_client(
                    service="redshift-serverless",
                    region=region,
                    temp_credentials=temp_credentials,
                )

                creds = redshift_serverless.get_credentials(
                    workgroupName=workgroup,
                    dbName=database,
                    durationSeconds=3600,
                )

            elif cluster_id is not None and cluster_id != "":
                logger.info(
                    f"cluster_id is provided, getting cluster_credentials for cluster_id: {cluster_id}"
                )
                creds = redshift.get_cluster_credentials(
                    DbUser=db_user,
                    DbName=database,
                    ClusterIdentifier=cluster_id,
                    AutoCreate=False,  # or True if you want to auto-create db user
                )

            elif cluster_id is None or cluster_id == "":
                # If cluster_id is not provided, get cluster_id from redshift irrespective of the deployment type
                logger.info(
                    "cluster_id is not provided, getting cluster_id from redshift"
                )
                cluster_id = get_cluster_credentials(redshift, credentials, extra)
                logger.info(f"cluster_id is {cluster_id}")

                if cluster_id is None or cluster_id == "":
                    raise ValueError("cluster_id or workgroup is required")

                else:
                    creds = redshift.get_cluster_credentials(
                        DbUser=db_user,
                        DbName=database,
                        ClusterIdentifier=cluster_id,
                        AutoCreate=False,  # or True if you want to auto-create db user
                    )
            else:
                # If workgroup is not provided, cluster_id cannot be found then throw the below error
                raise ValueError("cluster_id or workgroup is required")

            # --- Step 3: Build the SQLAlchemy connection string ---
            if "DbUser" in creds:
                username = quote_plus(creds["DbUser"])
            elif "dbUser" in creds:
                username = quote_plus(creds["dbUser"])
            else:
                raise ValueError("DbUser not found in creds")

            if "DbPassword" in creds:
                password = creds["DbPassword"]
            elif "dbPassword" in creds:
                password = creds["dbPassword"]
            else:
                raise ValueError("DbPassword not found in creds")

            conn_str = (
                f"redshift+psycopg2://{username}:{password}"
                f"@{host}:{port}/{database}"
            )
            # --- Step 4: Connect using SQLAlchemy ---
            assert self.DB_CONFIG is not None, "DB_CONFIG should not be None"
            self.engine = sqlalchemy.create_engine(
                conn_str, connect_args=self.DB_CONFIG.connect_args or {}
            )
            with self.engine.connect() as _:  # type: ignore
                pass
        else:
            await super().load(credentials)
