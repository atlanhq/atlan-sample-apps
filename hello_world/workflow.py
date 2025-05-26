import asyncio
from datetime import timedelta
from typing import Any, Callable, Coroutine, Dict, List, Sequence

from activities import HelloWorldActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.common.error_codes import ClientError, IOError, WorkflowError
from application_sdk.inputs.statestore import StateStoreInput
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import MetricType, get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

workflow.logger = get_logger(__name__)
workflow.traces = get_traces()
workflow.metrics = get_metrics()


@workflow.defn
class HelloWorldWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        This workflow is used to send a GIF to a list of recipients.

        Args:
            workflow_config (Dict[str, Any]): The workflow configuration

        Returns:
            None
        """
        try:
            if not workflow_config or "workflow_id" not in workflow_config:
                workflow.logger.error(
                    "Invalid workflow configuration",
                    extra={"error_code": ClientError.REQUEST_VALIDATION_ERROR.code},
                )
                raise ClientError.REQUEST_VALIDATION_ERROR

            workflow_id = workflow_config["workflow_id"]
            try:
                workflow_args: Dict[str, Any] = StateStoreInput.extract_configuration(
                    workflow_id
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

            activities_instance = HelloWorldActivities()

            name: str = workflow_args.get("name", "John Doe")
            workflow.logger.info("Starting hello world workflow")

            # Record metric for workflow start
            workflow.metrics.record_metric(
                name="hello_world_workflow_start",
                value=1.0,
                metric_type=MetricType.COUNTER,
                labels={
                    "workflow_id": workflow_id,
                    "name": name,
                    "workflow_type": "HelloWorldWorkflow",
                },
                description="Number of times hello world workflow is started",
                unit="count",
            )

            # Record trace for workflow execution
            workflow.traces.record_trace(
                name="hello_world_workflow",
                trace_id=workflow_id,
                span_id=f"{workflow_id}_main",
                kind="INTERNAL",
                status_code="OK",
                attributes={
                    "workflow_id": workflow_id,
                    "name": name,
                    "workflow_type": "HelloWorldWorkflow",
                    "service.name": "hello-world",
                    "service.version": "1.0.0",
                },
            )

            try:
                activities: List[Coroutine[Any, Any, Any]] = [
                    workflow.execute_activity(  # pyright: ignore[reportUnknownMemberType]
                        activities_instance.say_hello,
                        name,
                        start_to_close_timeout=timedelta(seconds=1000),
                    )
                ]

                # Wait for all activities to complete
                await asyncio.gather(*activities)
                workflow.logger.info("Hello world workflow completed")

                # Record metric for workflow completion
                workflow.metrics.record_metric(
                    name="hello_world_workflow_complete",
                    value=1.0,
                    metric_type=MetricType.COUNTER,
                    labels={
                        "workflow_id": workflow_id,
                        "name": name,
                        "workflow_type": "HelloWorldWorkflow",
                        "status": "success",
                    },
                    description="Number of times hello world workflow completes successfully",
                    unit="count",
                )

            except Exception as e:
                workflow.logger.error(
                    "Failed to execute workflow activities",
                    extra={
                        "error_code": WorkflowError.WORKFLOW_EXECUTION_ERROR.code,
                        "error": str(e),
                    },
                )
                # Record metric for workflow failure
                workflow.metrics.record_metric(
                    name="hello_world_workflow_complete",
                    value=1.0,
                    metric_type=MetricType.COUNTER,
                    labels={
                        "workflow_id": workflow_id,
                        "name": name,
                        "workflow_type": "HelloWorldWorkflow",
                        "status": "failure",
                    },
                    description="Number of times hello world workflow fails",
                    unit="count",
                )
                raise WorkflowError.WORKFLOW_EXECUTION_ERROR

        except Exception as e:
            workflow.logger.error(
                "Workflow execution failed",
                extra={
                    "error_code": WorkflowError.WORKFLOW_EXECUTION_ERROR.code,
                    "error": str(e),
                },
            )
            raise WorkflowError.WORKFLOW_EXECUTION_ERROR

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (ActivitiesInterface): The activities instance
                containing the hello world operations.

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods to be executed
                in order.
        """
        if not isinstance(activities, HelloWorldActivities):
            raise TypeError("Activities must be an instance of HelloWorldActivities")

        return [
            activities.say_hello,
        ]
