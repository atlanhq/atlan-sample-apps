"""
This file contains the activities for the SQL metadata extraction application.

Note:
- The fetch_columns activity fetches the columns from the source database it is overridden from the base class for demonstration purposes.
"""

from typing import Any, Dict, Optional, cast

from application_sdk.activities.common.models import ActivityStatistics
from application_sdk.activities.common.utils import auto_heartbeater
from application_sdk.activities.metadata_extraction.sql import (
    BaseSQLMetadataExtractionActivities,
    BaseSQLMetadataExtractionActivitiesState,
)
from application_sdk.common.utils import prepare_query
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.services.secretstore import SecretStore
from sqlalchemy import text
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger
metrics = get_metrics()
traces = get_traces()


class SQLMetadataExtractionActivities(BaseSQLMetadataExtractionActivities):
    async def _validate_filter_configuration(
        self,
        workflow_args: Dict[str, Any],
        state: BaseSQLMetadataExtractionActivitiesState,
    ) -> Dict[str, Any]:
        """Validate that the configured filters match at least some schemas/tables.

        Args:
            workflow_args: The workflow arguments containing filter configuration.
            state: The activity state containing the SQL client.

        Returns:
            Dict containing validation results with keys:
                - has_schemas: bool indicating if any schemas match the filters
                - has_tables: bool indicating if any tables match the filters
                - schema_count: number of schemas matching filters
                - table_count: number of tables matching filters
        """
        if not state.sql_client or not state.sql_client.engine:
            logger.error(
                "SQL client or engine not initialized during filter validation"
            )
            return {
                "has_schemas": False,
                "has_tables": False,
                "schema_count": 0,
                "table_count": 0,
                "error": "SQL client not initialized",
            }

        try:
            # Check if any schemas match the filters
            schema_query = prepare_query(
                query=self.fetch_schema_sql, workflow_args=workflow_args
            )

            async with state.sql_client.engine.begin() as conn:
                schema_result = await conn.execute(text(schema_query))
                schema_count = len(schema_result.fetchall())

            # Check if any tables match the filters
            table_check_query = prepare_query(
                query=self.tables_check_sql, workflow_args=workflow_args
            )

            async with state.sql_client.engine.begin() as conn:
                table_result = await conn.execute(text(table_check_query))
                table_row = table_result.fetchone()
                table_count = table_row[0] if table_row else 0

            return {
                "has_schemas": schema_count > 0,
                "has_tables": table_count > 0,
                "schema_count": schema_count,
                "table_count": table_count,
            }
        except Exception as e:
            logger.error(
                "Error validating filter configuration",
                exc_info=True,
                extra={"error": str(e)},
            )
            return {
                "has_schemas": False,
                "has_tables": False,
                "schema_count": 0,
                "table_count": 0,
                "error": str(e),
            }

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def preflight_check(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Enhanced preflight check that validates filter configuration.

        This method extends the base preflight check to validate that the configured
        include/exclude filters will match at least some metadata in the source database.

        Args:
            workflow_args: The workflow arguments.

        Returns:
            Optional[ActivityStatistics]: The activity statistics.

        Raises:
            ValueError: If filters are configured but match no metadata.
        """
        # First run the base preflight check
        result = await super().preflight_check(workflow_args)

        # Get state to access the SQL client
        state = cast(
            BaseSQLMetadataExtractionActivitiesState,
            await self._get_state(workflow_args),
        )

        # Validate filter configuration
        validation_result = await self._validate_filter_configuration(
            workflow_args, state
        )

        if "error" in validation_result:
            logger.warning(
                "Filter validation check encountered an error but will continue",
                extra={"error": validation_result["error"]},
            )
            return result

        # Log validation results
        logger.info(
            "Filter validation results",
            extra={
                "schema_count": validation_result["schema_count"],
                "table_count": validation_result["table_count"],
                "has_schemas": validation_result["has_schemas"],
                "has_tables": validation_result["has_tables"],
            },
        )

        # Warn if no schemas or tables match the filters
        if not validation_result["has_schemas"]:
            logger.warning(
                "CONFIGURATION WARNING: Include/exclude filters match ZERO schemas. "
                "This extraction will produce no metadata. "
                "Please review your filter configuration.",
                extra={
                    "include_filter": workflow_args.get("metadata", {}).get(
                        "include_filter"
                    ),
                    "exclude_filter": workflow_args.get("metadata", {}).get(
                        "exclude_filter"
                    ),
                },
            )

        if not validation_result["has_tables"]:
            logger.warning(
                "CONFIGURATION WARNING: Include/exclude filters match ZERO tables. "
                "This extraction will produce no metadata. "
                "Please review your filter configuration and temp-table-regex settings.",
                extra={
                    "include_filter": workflow_args.get("metadata", {}).get(
                        "include_filter"
                    ),
                    "exclude_filter": workflow_args.get("metadata", {}).get(
                        "exclude_filter"
                    ),
                    "temp_table_regex": workflow_args.get("metadata", {}).get(
                        "temp-table-regex"
                    ),
                },
            )

        return result

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def credential_extraction_demo_activity(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """A custom activity demostrating the use of various utilities provided by the application SDK.

        Args:
            workflow_args: The workflow arguments.

        Returns:
            Optional[ActivityStatistics]: The activity statistics.
        """

        # reference to credentials passed as user inputs are available as 'credential_guid' in workflow_args
        # in this case refer to https://github.com/atlanhq/atlan-sample-apps/blob/main/connectors/mysql/frontend/static/script.js#L740
        await SecretStore.get_credentials(workflow_args["credential_guid"])
        logger.info("credentials retrieved successfully")

        return None

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_columns(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch columns from the source database.

        Args:
            batch_input: DataFrame containing the raw column data.
            raw_output: JsonOutput instance for writing raw data.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[ActivityStatistics]: Statistics about the extracted columns, or None if extraction failed.
        """
        state = cast(
            BaseSQLMetadataExtractionActivitiesState,
            await self._get_state(workflow_args),
        )
        if not state.sql_client or not state.sql_client.engine:
            logger.error("SQL client or engine not initialized")
            raise ValueError("SQL client or engine not initialized")

        prepared_query = prepare_query(
            query=self.fetch_column_sql, workflow_args=workflow_args
        )
        statistics = await self.query_executor(
            sql_engine=state.sql_client.engine,
            sql_query=prepared_query,
            workflow_args=workflow_args,
            output_suffix="raw/column",
            typename="column",
        )

        # Log warning if no columns were extracted
        if statistics and statistics.get("records", 0) == 0:
            logger.warning(
                "EXTRACTION WARNING: Zero columns extracted. "
                "This may indicate misconfigured filters or an empty source database.",
                extra={
                    "activity": "fetch_columns",
                    "include_filter": workflow_args.get("metadata", {}).get(
                        "include_filter"
                    ),
                    "exclude_filter": workflow_args.get("metadata", {}).get(
                        "exclude_filter"
                    ),
                    "temp_table_regex": workflow_args.get("metadata", {}).get(
                        "temp-table-regex"
                    ),
                },
            )

        return statistics

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_tables(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch tables from the source database with zero-record validation.

        Args:
            workflow_args: The workflow arguments.

        Returns:
            Optional[ActivityStatistics]: Statistics about the extracted tables.
        """
        statistics = await super().fetch_tables(workflow_args)

        # Log warning if no tables were extracted
        if statistics and statistics.get("records", 0) == 0:
            logger.warning(
                "EXTRACTION WARNING: Zero tables extracted. "
                "This may indicate misconfigured filters or an empty source database.",
                extra={
                    "activity": "fetch_tables",
                    "include_filter": workflow_args.get("metadata", {}).get(
                        "include_filter"
                    ),
                    "exclude_filter": workflow_args.get("metadata", {}).get(
                        "exclude_filter"
                    ),
                    "temp_table_regex": workflow_args.get("metadata", {}).get(
                        "temp-table-regex"
                    ),
                },
            )

        return statistics

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_schemas(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch schemas from the source database with zero-record validation.

        Args:
            workflow_args: The workflow arguments.

        Returns:
            Optional[ActivityStatistics]: Statistics about the extracted schemas.
        """
        statistics = await super().fetch_schemas(workflow_args)

        # Log warning if no schemas were extracted
        if statistics and statistics.get("records", 0) == 0:
            logger.warning(
                "EXTRACTION WARNING: Zero schemas extracted. "
                "This may indicate misconfigured filters or an empty source database.",
                extra={
                    "activity": "fetch_schemas",
                    "include_filter": workflow_args.get("metadata", {}).get(
                        "include_filter"
                    ),
                    "exclude_filter": workflow_args.get("metadata", {}).get(
                        "exclude_filter"
                    ),
                },
            )

        return statistics

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_databases(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch databases from the source database with zero-record validation.

        Args:
            workflow_args: The workflow arguments.

        Returns:
            Optional[ActivityStatistics]: Statistics about the extracted databases.
        """
        statistics = await super().fetch_databases(workflow_args)

        # Log warning if no databases were extracted
        if statistics and statistics.get("records", 0) == 0:
            logger.warning(
                "EXTRACTION WARNING: Zero databases extracted. "
                "The source may only contain system databases (information_schema, performance_schema, mysql, sys) "
                "which are automatically excluded from extraction.",
                extra={"activity": "fetch_databases"},
            )

        return statistics
