from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import DqPocActivities
from app.models import DqPocResult
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

logger = get_logger(__name__)
workflow.logger = logger
metrics = get_metrics()
traces = get_traces()


@workflow.defn
class DqPocWorkflow(WorkflowInterface):
    @observability(logger=logger, metrics=metrics, traces=traces)
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> DqPocResult:
        """
        This workflow is used to run a dq poc sample application.

        Args:
            workflow_config (Dict[str, Any]): The workflow configuration

        Returns:
            DqPocResult: The result of the dq poc sample application
        """
        activities_instance = DqPocActivities()

        logger.info("Starting dq poc sample application")

        await workflow.execute_activity(
            activities_instance.run_dq_poc_sync,
            start_to_close_timeout=timedelta(seconds=5),
        )

        result = DqPocResult()
        result.result = 1
        logger.info(f"Dq poc sample application result: {result}")
        logger.info("Dq poc sample application completed")
        return result

    @staticmethod
    def get_activities(
        activities: ActivitiesInterface,
    ) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (ActivitiesInterface): The activities instance
                containing the dq poc sample application operations.

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods to be
                executed in order.
        """
        if not isinstance(activities, DqPocActivities):
            raise TypeError("Activities must be an instance of DqPocActivities")

        return [activities.run_dq_poc_sync]
