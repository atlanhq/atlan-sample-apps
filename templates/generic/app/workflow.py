from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import ActivitiesClass
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

logger = get_logger(__name__)
workflow.logger = logger


@workflow.defn
class WorkflowClass(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        Orchestrate the workflow summary flow:

        1. Read workflow args (supports username, city, units with defaults)
        2. Fetch and format current metadata via activities
        3. Log the summary
        """
        activities_instance = ActivitiesClass()

        # Merge any provided args (from frontend POST body or server config)
        _workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Call other activities here
        pass

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """
        Declare which activity methods are part of this workflow for the worker.
        """
        if not isinstance(activities, ActivitiesClass):
            raise TypeError("Activities must be an instance of ActivitiesClass")

        return [
            activities.get_workflow_args
            # List other activities here
        ]
