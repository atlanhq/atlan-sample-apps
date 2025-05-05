import asyncio
from datetime import timedelta
from typing import Any, Callable, Coroutine, Dict, List, Sequence

from application_sdk.activities import ActivitiesInterface
from application_sdk.common.logger_adaptors import get_logger
from application_sdk.inputs.statestore import StateStoreInput
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

from activities import HelloWorldActivities

workflow.logger = get_logger(__name__)


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
        workflow_id = workflow_config["workflow_id"]
        workflow_args: Dict[str, Any] = StateStoreInput.extract_configuration(
            workflow_id
        )
        activities_instance = HelloWorldActivities()

        name: str = workflow_args.get("name", "John Doe")
        workflow.logger.info("Starting hello world workflow")

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
