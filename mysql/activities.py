"""
This file contains the activities for the SQL metadata extraction application.

Note:
- The fetch_columns activity fetches the columns from the source database it is overridden from the base class for demonstration purposes.
"""

import time
from typing import Any, Dict, Optional, cast

from application_sdk.activities.common.models import ActivityStatistics
from application_sdk.activities.common.utils import auto_heartbeater
from application_sdk.activities.metadata_extraction.sql import (
    BaseSQLMetadataExtractionActivities,
    BaseSQLMetadataExtractionActivitiesState,
)
from application_sdk.common.error_codes import (
    ActivityError,
    ClientError,
    IOError,
    OrchestratorError,
)
from application_sdk.common.utils import prepare_query
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import MetricType, get_metrics
from application_sdk.observability.traces_adaptor import TracingContext, get_traces
from temporalio import activity

logger = get_logger(__name__)
activity.traces = get_traces()
activity.metrics = get_metrics()


class SQLMetadataExtractionActivities(BaseSQLMetadataExtractionActivities):
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
        start_time = time.time()
        try:
            state = cast(
                BaseSQLMetadataExtractionActivitiesState,
                await self._get_state(workflow_args),
            )
            if not state.sql_client or not state.sql_client.engine:
                logger.error(
                    "SQL client or engine not initialized",
                    extra={"error_code": ClientError.SQL_CLIENT_AUTH_ERROR.code},
                )
                raise ClientError.SQL_CLIENT_AUTH_ERROR

            # Create tracing context
            tracing = TracingContext(
                logger,
                activity.metrics,
                activity.traces,
                trace_id=activity.info().workflow_id,
                root_span_id=activity.info().activity_id,
            )

            # Record activity start metric
            activity.metrics.record_metric(
                name="sql_metadata_fetch_columns_start",
                value=1.0,
                metric_type=MetricType.COUNTER,
                labels={
                    "workflow_id": activity.info().workflow_id,
                    "activity_id": activity.info().activity_id,
                    "status": "started",
                },
                description="SQL metadata fetch columns activity start counter",
                unit="count",
            )

            try:
                async with tracing.trace_operation(
                    "prepare_query", "Preparing SQL query"
                ):
                    prepared_query = prepare_query(
                        query=self.fetch_column_sql, workflow_args=workflow_args
                    )
            except Exception as e:
                logger.error(
                    "Failed to prepare SQL query",
                    extra={"error_code": IOError.SQL_QUERY_ERROR.code, "error": str(e)},
                )
                raise IOError.SQL_QUERY_ERROR

            try:
                async with tracing.trace_operation(
                    "execute_query", "Executing SQL query"
                ):
                    statistics = await self.query_executor(
                        sql_engine=state.sql_client.engine,
                        sql_query=prepared_query,
                        workflow_args=workflow_args,
                        output_suffix="raw/column",
                        typename="column",
                    )
            except Exception as e:
                logger.error(
                    "Failed to execute SQL query",
                    extra={
                        "error_code": ActivityError.QUERY_EXTRACTION_SQL_ERROR.code,
                        "error": str(e),
                    },
                )
                raise ActivityError.QUERY_EXTRACTION_SQL_ERROR

            # Record activity completion metric with statistics
            if statistics:
                activity.metrics.record_metric(
                    name="sql_metadata_fetch_columns_complete",
                    value=1.0,
                    metric_type=MetricType.COUNTER,
                    labels={
                        "workflow_id": activity.info().workflow_id,
                        "activity_id": activity.info().activity_id,
                        "status": "completed",
                        "rows_processed": str(statistics.rows_processed),
                        "rows_written": str(statistics.rows_written),
                    },
                    description="SQL metadata fetch columns activity completion counter",
                    unit="count",
                )

                # Record activity duration
                total_duration = (time.time() - start_time) * 1000
                activity.metrics.record_metric(
                    name="sql_metadata_fetch_columns_duration",
                    value=total_duration,
                    metric_type=MetricType.HISTOGRAM,
                    labels={
                        "workflow_id": activity.info().workflow_id,
                        "activity_id": activity.info().activity_id,
                        "status": "success",
                        "rows_processed": str(statistics.rows_processed),
                        "rows_written": str(statistics.rows_written),
                    },
                    description="SQL metadata fetch columns activity duration",
                    unit="milliseconds",
                )

            return statistics

        except Exception as e:
            # Record activity failure duration
            total_duration = (time.time() - start_time) * 1000
            activity.metrics.record_metric(
                name="sql_metadata_fetch_columns_duration",
                value=total_duration,
                metric_type=MetricType.HISTOGRAM,
                labels={
                    "workflow_id": activity.info().workflow_id,
                    "activity_id": activity.info().activity_id,
                    "status": "failure",
                },
                description="SQL metadata fetch columns activity duration",
                unit="milliseconds",
            )

            logger.error(
                "Activity execution failed",
                extra={
                    "error_code": OrchestratorError.TEMPORAL_CLIENT_ACTIVITY_ERROR.code,
                    "error": str(e),
                },
            )
            raise OrchestratorError.TEMPORAL_CLIENT_ACTIVITY_ERROR
