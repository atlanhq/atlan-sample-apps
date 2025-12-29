"""Workflow for simple hello world app."""

from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import SimpleHelloActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow


@workflow.defn
class SimpleHelloWorkflow(WorkflowInterface):
    """Simple workflow that outputs Hello World."""

    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """Run the simple hello world workflow.

        Args:
            workflow_config (Dict[str, Any]): The workflow configuration
        """
        activities_instance = SimpleHelloActivities()

        await workflow.execute_activity(
            activities_instance.output_hello_world,
            start_to_close_timeout=timedelta(seconds=5),
        )

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (ActivitiesInterface): The activities instance

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods to be executed
        """
        if not isinstance(activities, SimpleHelloActivities):
            raise TypeError("Activities must be an instance of SimpleHelloActivities")

        return [
            activities.output_hello_world,
        ]

