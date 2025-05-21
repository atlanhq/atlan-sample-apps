"""
This file contains the workflow definition for the SQL metadata extraction application.

Note:
- The run method is overriden from the base class for demostration purposes.
"""

import asyncio
from typing import Any, Callable, Dict, List

from activities import SQLMetadataExtractionActivities
from application_sdk.inputs.statestore import StateStoreInput
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.workflows.metadata_extraction.sql import (
    BaseSQLMetadataExtractionWorkflow,
)
from temporalio import workflow
from temporalio.common import RetryPolicy

logger = get_logger(__name__)
workflow.traces = get_traces()
workflow.metrics = get_metrics()


@workflow.defn
class SQLMetadataExtractionWorkflow(BaseSQLMetadataExtractionWorkflow):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]):
        """
        Run the workflow.

        :param workflow_args: The workflow arguments.
        """
        workflow_id = workflow_config["workflow_id"]
        workflow_args: Dict[str, Any] = StateStoreInput.extract_configuration(
            workflow_id
        )

        workflow_run_id = workflow.info().run_id
        workflow_args["workflow_run_id"] = workflow_run_id

        workflow.logger.info(f"Starting extraction workflow for {workflow_id}")

        # Record workflow start metric
        workflow.metrics.record_metric(
            name="sql_metadata_extraction_workflow_start",
            value=1.0,
            metric_type="counter",
            labels={
                "workflow_id": workflow_id,
                "workflow_run_id": workflow_run_id,
                "status": "started",
            },
            description="SQL metadata extraction workflow start counter",
            unit="count",
        )

        retry_policy = RetryPolicy(
            maximum_attempts=6,
            backoff_coefficient=2,
        )

        output_prefix = workflow_args["output_prefix"]
        output_path = f"{output_prefix}/{workflow_id}/{workflow_run_id}"
        workflow_args["output_path"] = output_path

        # Add trace for workflow execution
        with workflow.traces.record_trace(
            name="sql_metadata_extraction_workflow",
            trace_id=workflow_id,
            span_id=f"{workflow_id}_main",
            kind="INTERNAL",
            status_code="OK",
            attributes={
                "workflow_id": workflow_id,
                "workflow_run_id": workflow_run_id,
                "output_path": output_path,
                "workflow_type": "SQLMetadataExtractionWorkflow",
            },
        ):
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

            # Record workflow completion metric
            workflow.metrics.record_metric(
                name="sql_metadata_extraction_workflow_complete",
                value=1.0,
                metric_type="counter",
                labels={
                    "workflow_id": workflow_id,
                    "workflow_run_id": workflow_run_id,
                    "status": "completed",
                },
                description="SQL metadata extraction workflow completion counter",
                unit="count",
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
            activities.preflight_check,
            activities.fetch_databases,
            activities.fetch_schemas,
            activities.fetch_tables,
            activities.fetch_columns,
            activities.transform_data,
        ]
