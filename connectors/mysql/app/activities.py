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
from application_sdk.common.credential_utils import get_credentials
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger
metrics = get_metrics()
traces = get_traces()


class SQLMetadataExtractionActivities(BaseSQLMetadataExtractionActivities):
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
        credentials = await get_credentials(workflow_args["credential_guid"])
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

        return statistics
