"""
This file contains the workflow definition for the SQL metadata extraction application.

Note:
- The run method is overriden from the base class for demostration purposes.
"""

import asyncio
import time
from typing import Any, Callable, Dict, List

from activities import SQLMetadataExtractionActivities
from application_sdk.common.error_codes import ClientError, IOError, WorkflowError
from application_sdk.inputs.statestore import StateStoreInput
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import MetricType, get_metrics
from application_sdk.observability.traces_adaptor import TracingContext, get_traces
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
        start_time = time.time()
        workflow_id = None

        try:
            if not workflow_config or "workflow_id" not in workflow_config:
                workflow.logger.error(
                    "Invalid workflow configuration",
                    extra={"error_code": ClientError.REQUEST_VALIDATION_ERROR.code},
                )
                raise ClientError.REQUEST_VALIDATION_ERROR

            workflow_id = workflow_config["workflow_id"]

            # Create tracing context
            tracing = TracingContext(
                workflow.logger,
                workflow.metrics,
                workflow.traces,
                trace_id=workflow_id,
                root_span_id=f"{workflow_id}_main",
            )

            try:
                async with tracing.trace_operation(
                    "extract_config", "Extracting workflow configuration"
                ):
                    workflow_args: Dict[str, Any] = (
                        StateStoreInput.extract_configuration(workflow_id)
                    )
            except Exception as e:
                workflow.logger.error(
                    "Failed to extract workflow configuration",
                    extra={
                        "error_code": IOError.STATE_STORE_EXTRACT_ERROR.code,
                        "error": str(e),
                    },
                )
                raise IOError.STATE_STORE_EXTRACT_ERROR

            workflow_run_id = workflow.info().run_id
            workflow_args["workflow_run_id"] = workflow_run_id

            workflow.logger.info(f"Starting extraction workflow for {workflow_id}")

            # Record workflow start metric
            workflow.metrics.record_metric(
                name="sql_metadata_extraction_workflow_start",
                value=1.0,
                metric_type=MetricType.COUNTER,
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

            async with tracing.trace_operation(
                "preflight_check", "Running preflight check"
            ):
                await workflow.execute_activity_method(
                    self.activities_cls.preflight_check,
                    workflow_args,
                    retry_policy=retry_policy,
                    start_to_close_timeout=self.default_start_to_close_timeout,
                    heartbeat_timeout=self.default_heartbeat_timeout,
                )

            async with tracing.trace_operation(
                "fetch_and_transform", "Fetching and transforming data"
            ):
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
                metric_type=MetricType.COUNTER,
                labels={
                    "workflow_id": workflow_id,
                    "workflow_run_id": workflow_run_id,
                    "status": "completed",
                },
                description="SQL metadata extraction workflow completion counter",
                unit="count",
            )

            # Record workflow duration
            total_duration = (time.time() - start_time) * 1000
            workflow.metrics.record_metric(
                name="sql_metadata_extraction_workflow_duration",
                value=total_duration,
                metric_type=MetricType.HISTOGRAM,
                labels={
                    "workflow_id": workflow_id,
                    "workflow_run_id": workflow_run_id,
                    "status": "success",
                },
                description="Workflow execution duration",
                unit="milliseconds",
            )

        except Exception as e:
            if workflow_id:
                total_duration = (time.time() - start_time) * 1000
                workflow.metrics.record_metric(
                    name="sql_metadata_extraction_workflow_duration",
                    value=total_duration,
                    metric_type=MetricType.HISTOGRAM,
                    labels={
                        "workflow_id": workflow_id,
                        "workflow_run_id": workflow.info().run_id
                        if workflow.info()
                        else "unknown",
                        "status": "failure",
                    },
                    description="Workflow execution duration",
                    unit="milliseconds",
                )

            workflow.logger.error(
                "Workflow execution failed",
                extra={
                    "error_code": WorkflowError.WORKFLOW_EXECUTION_ERROR.code,
                    "error": str(e),
                },
            )
            raise WorkflowError.WORKFLOW_EXECUTION_ERROR

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
