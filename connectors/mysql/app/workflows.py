"""
This file contains the workflow definition for the SQL metadata extraction application.

Note:
- The run method is overriden from the base class for demostration purposes.
"""

import asyncio
from datetime import timedelta
from typing import Any, Callable, Dict, List

from app.activities import SQLMetadataExtractionActivities
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.workflows.metadata_extraction.sql import (
    BaseSQLMetadataExtractionWorkflow,
)
from temporalio import workflow
from temporalio.common import RetryPolicy

logger = get_logger(__name__)
workflow.logger = logger
metrics = get_metrics()
traces = get_traces()


@workflow.defn
class SQLMetadataExtractionWorkflow(BaseSQLMetadataExtractionWorkflow):
    @observability(logger=logger, metrics=metrics, traces=traces)
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]):
        """
        Run the workflow.

        :param workflow_args: The workflow arguments.
        """
        activities_instance = SQLMetadataExtractionActivities()

        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        retry_policy = RetryPolicy(
            maximum_attempts=6,
            backoff_coefficient=2,
        )

        await workflow.execute_activity_method(
            activities_instance.preflight_check,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        await workflow.execute_activity_method(
            activities_instance.credential_extraction_demo_activity,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        # Execute all extraction activities and collect statistics
        fetch_and_transforms = [
            self.fetch_and_transform(
                activities_instance.fetch_databases,
                workflow_args,
                retry_policy,
            ),
            self.fetch_and_transform(
                activities_instance.fetch_schemas,
                workflow_args,
                retry_policy,
            ),
            self.fetch_and_transform(
                activities_instance.fetch_tables,
                workflow_args,
                retry_policy,
            ),
            self.fetch_and_transform(
                activities_instance.fetch_columns,
                workflow_args,
                retry_policy,
            ),
        ]
        results = await asyncio.gather(*fetch_and_transforms)

        # Check if all extractions returned zero records
        total_records = sum(
            result.get("records", 0) if result else 0 for result in results
        )

        if total_records == 0:
            logger.error(
                "EXTRACTION FAILED: Zero metadata records extracted across all activities. "
                "This is likely a configuration issue. "
                "Common causes: "
                "1) Include/exclude filters don't match any schemas/tables in the source, "
                "2) Source database is empty or contains only system schemas, "
                "3) Incorrect database connection or credentials pointing to wrong instance. "
                "Please review your configuration and filters.",
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
                    "database_statistics": results[0] if len(results) > 0 else None,
                    "schema_statistics": results[1] if len(results) > 1 else None,
                    "table_statistics": results[2] if len(results) > 2 else None,
                    "column_statistics": results[3] if len(results) > 3 else None,
                },
            )
        else:
            logger.info(
                "Extraction completed successfully",
                extra={
                    "total_records": total_records,
                    "database_records": results[0].get("records", 0)
                    if results[0]
                    else 0,
                    "schema_records": results[1].get("records", 0) if results[1] else 0,
                    "table_records": results[2].get("records", 0) if results[2] else 0,
                    "column_records": results[3].get("records", 0) if results[3] else 0,
                },
            )

    @staticmethod
    def get_activities(
        activities: SQLMetadataExtractionActivities,
    ) -> List[Callable[..., Any]]:
        """Get the list of activities for the workflow.

        Args:
            activities: The activities instance containing the workflow activities.

        Returns:
            List[Callable[..., Any]]: A list of activity methods that can be executed by the workflow.
        """
        return [
            activities.get_workflow_args,
            activities.preflight_check,
            activities.fetch_databases,
            activities.fetch_schemas,
            activities.fetch_tables,
            activities.fetch_columns,
            activities.credential_extraction_demo_activity,
            activities.transform_data,
        ]
