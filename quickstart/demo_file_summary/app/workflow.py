import asyncio
from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import FileSummaryActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow
from temporalio.common import RetryPolicy

logger = get_logger(__name__)
workflow.logger = logger
metrics = get_metrics()
traces = get_traces()


@workflow.defn
class FileSummaryWorkflow(WorkflowInterface):
    @observability(logger=logger, metrics=metrics, traces=traces)
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        Workflow to read JSON input, count status occurrences, and write summary.

        Args:
            workflow_config (Dict[str, Any]): The workflow configuration containing
                input_file and output_file paths

        Returns:
            None
        """
        logger.info("Starting file summary workflow")

        activities_instance = FileSummaryActivities()

        retry_policy = RetryPolicy(
            maximum_attempts=3,
            backoff_coefficient=2,
        )

        # Get workflow args from state store
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Execute the summarize activity
        status_counts = await workflow.execute_activity(
            activities_instance.summarize_status_counts,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(seconds=30),
        )

        logger.info(f"Workflow completed. Status counts: {status_counts}")

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (ActivitiesInterface): The activities instance

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods
        """
        if not isinstance(activities, FileSummaryActivities):
            raise TypeError("Activities must be an instance of FileSummaryActivities")

        return [
            activities.summarize_status_counts,
            activities.get_workflow_args,
        ]
