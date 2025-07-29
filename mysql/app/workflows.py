"""
This file contains the workflow definition for the SQL metadata extraction application.

Note:
- The run method is overriden from the base class for demostration purposes.
"""

import asyncio
from datetime import timedelta
from typing import Any, Callable, Dict, List

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

from mysql.app.activities import SQLMetadataExtractionActivities

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
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            self.activities_cls.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        retry_policy = RetryPolicy(
            maximum_attempts=6,
            backoff_coefficient=2,
        )

        await workflow.execute_activity_method(
            self.activities_cls.preflight_check,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        fetch_and_transforms = [
            self.fetch_and_transform(
                self.activities_cls.fetch_databases,
                workflow_args,
                retry_policy,
            ),
            self.fetch_and_transform(
                self.activities_cls.fetch_schemas,
                workflow_args,
                retry_policy,
            ),
            self.fetch_and_transform(
                self.activities_cls.fetch_tables,
                workflow_args,
                retry_policy,
            ),
            self.fetch_and_transform(
                self.activities_cls.fetch_columns,
                workflow_args,
                retry_policy,
            ),
        ]
        await asyncio.gather(*fetch_and_transforms)

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
            activities.transform_data,
        ]
