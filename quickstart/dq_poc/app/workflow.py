from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import DqPocActivities
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
    async def run(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        This workflow is used to run a dq poc sample application.

        Args:
            workflow_config (Dict[str, Any]): The workflow configuration

        Returns:
            Dict[str, Any]: Dummy result payload returned from the activity
        """
        activities_instance = DqPocActivities()

        logger.info("Starting dq poc sample application")

        # Fetch the full request payload from the SDK state store.
        # The HTTP API starts the workflow with {"workflow_id": ...} only.
        # The SDK stores the full request body under that workflow_id.
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )
        logger.info(f"Workflow args is as follows: {workflow_args}")
        # Pass the full request payload into the activity and get its dummy
        # result.
        result: Dict[str, Any] = await workflow.execute_activity(
            activities_instance.run_dq_poc_sync,
            workflow_args,
            start_to_close_timeout=timedelta(seconds=10),
        )

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

        return [
            activities.get_workflow_args,
            activities.run_dq_poc_sync,
        ]
