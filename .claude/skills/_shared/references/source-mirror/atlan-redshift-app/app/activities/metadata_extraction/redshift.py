import os
from typing import Any, Dict, cast

from application_sdk.activities.common.utils import auto_heartbeater
from application_sdk.activities.metadata_extraction.sql import (
    BaseSQLMetadataExtractionActivities,
    BaseSQLMetadataExtractionActivitiesState,
)
from application_sdk.common.utils import read_sql_files
from application_sdk.constants import SQL_QUERIES_PATH
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.services.statestore import StateStore, StateType
from temporalio import activity

from app.activities.metadata_extraction.utils import resolve_cloned_sql
from app.clients import RedshiftClient

logger = get_logger(__name__)
activity.logger = logger

# Load Redshift-specific SQL queries from app/sql
queries = read_sql_files(queries_prefix=SQL_QUERIES_PATH)


class RedshiftSQLMetadataExtractionActivities(BaseSQLMetadataExtractionActivities):
    """
    Redshift-specific metadata extraction activities, allowing dynamic SQL selection.
    """

    sql_client_class = RedshiftClient

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        # Ensure multidb mode is enabled while preserving upstream kwargs
        kwargs.setdefault("multidb", True)
        super().__init__(*args, **kwargs)

    @activity.defn
    @auto_heartbeater
    async def fetch_databases(self, workflow_args):  # type: ignore
        """Fetch databases with schema count using extract_database_with_schema_count.sql query.

        Uses base query_executor in multidb mode to execute across databases.
        """
        # Load the database extraction SQL with schema count
        database_sql = queries.get("EXTRACT_DATABASE_WITH_SCHEMA_COUNT")
        if not database_sql:
            raise ValueError("EXTRACT_DATABASE_WITH_SCHEMA_COUNT SQL query not found")

        state = cast(
            BaseSQLMetadataExtractionActivitiesState,
            await self._get_state(workflow_args),
        )

        # Use base query executor in multidb mode
        if not state.sql_client:
            logger.error("SQL client not initialized")
            raise ValueError("SQL client not initialized")
        output_path = os.path.join(workflow_args.get("output_path", ""), "raw")
        return await self.query_executor(
            sql_client=state.sql_client,
            sql_query=database_sql,
            workflow_args=workflow_args,
            output_path=output_path,
            typename="database",
            write_to_file=False,
            concatenate=True,
        )

    @activity.defn
    @auto_heartbeater
    async def fetch_tables(self, workflow_args):  # type: ignore
        self.fetch_table_sql = resolve_cloned_sql(
            workflow_args=workflow_args,
            default_sql=self.fetch_table_sql,
        )
        state = cast(
            BaseSQLMetadataExtractionActivitiesState,
            await self._get_state(workflow_args),
        )
        if not state.sql_client:
            logger.error("SQL client not initialized")
            raise ValueError("SQL client not initialized")
        output_path = os.path.join(workflow_args.get("output_path", ""), "raw")
        return await self.query_executor(
            sql_client=state.sql_client,
            sql_query=self.fetch_table_sql,
            workflow_args=workflow_args,
            output_path=output_path,
            typename="table",
        )

    @activity.defn
    @auto_heartbeater
    async def fetch_schemas(self, workflow_args):  # type: ignore
        self.fetch_schema_sql = resolve_cloned_sql(
            workflow_args=workflow_args,
            default_sql=self.fetch_schema_sql,
        )
        state = cast(
            BaseSQLMetadataExtractionActivitiesState,
            await self._get_state(workflow_args),
        )
        if not state.sql_client:
            logger.error("SQL client not initialized")
            raise ValueError("SQL client not initialized")
        output_path = os.path.join(workflow_args.get("output_path", ""), "raw")
        return await self.query_executor(
            sql_client=state.sql_client,
            sql_query=self.fetch_schema_sql,
            workflow_args=workflow_args,
            output_path=output_path,
            typename="schema",
        )

    @activity.defn
    @auto_heartbeater
    async def fetch_columns(self, workflow_args):  # type: ignore
        self.fetch_column_sql = resolve_cloned_sql(
            workflow_args=workflow_args,
            default_sql=self.fetch_column_sql,
        )
        state = cast(
            BaseSQLMetadataExtractionActivitiesState,
            await self._get_state(workflow_args),
        )
        if not state.sql_client:
            logger.error("SQL client not initialized")
            raise ValueError("SQL client not initialized")
        output_path = os.path.join(workflow_args.get("output_path", ""), "raw")
        return await self.query_executor(
            sql_client=state.sql_client,
            sql_query=self.fetch_column_sql,
            workflow_args=workflow_args,
            output_path=output_path,
            typename="column",
        )

    @activity.defn
    @auto_heartbeater
    async def save_workflow_state(
        self, workflow_id: str, workflow_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Activity to save workflow state to the state store.

        This activity is used to save workflow arguments to the state store
        from within a workflow context, avoiding the restriction on using
        file operations directly in workflows.

        Args:
            workflow_id: The ID of the workflow.
            workflow_args: The workflow arguments to save.

        Returns:
            Dict[str, Any]: The updated state.

        Raises:
            Exception: If there's an error saving the state.
        """
        try:
            return await StateStore.save_state_object(
                id=workflow_id, value=workflow_args, type=StateType.WORKFLOWS
            )
        except Exception as e:
            logger.error(f"Failed to save workflow state for {workflow_id}: {str(e)}")
            raise
