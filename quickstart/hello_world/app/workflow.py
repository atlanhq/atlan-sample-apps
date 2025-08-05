import asyncio
from datetime import timedelta
from typing import Any, Callable, Coroutine, Dict, List, Sequence

from app.activities import HelloWorldActivities
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
class HelloWorldWorkflow(WorkflowInterface):
    @observability(logger=logger, metrics=metrics, traces=traces)
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        This workflow is used to say hello to a name.

        Args:
            workflow_config (Dict[str, Any]): The workflow configuration

        Returns:
            None
        """
        activities_instance = HelloWorldActivities()

        # Get the workflow configuration from the state store
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        name: str = workflow_args.get("name", "John Doe")
        logger.info("Starting hello world workflow")

        activities: List[Coroutine[Any, Any, Any]] = [
            workflow.execute_activity(  # pyright: ignore[reportUnknownMemberType]
                activities_instance.say_hello,
                name,
                start_to_close_timeout=timedelta(seconds=5),
            )
        ]

        # Wait for all activities to complete
        await asyncio.gather(*activities)

        await workflow.execute_activity(
            activities_instance.say_hello_sync,
            name,
            start_to_close_timeout=timedelta(seconds=5),
        )

        logger.info("Hello world workflow completed")

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
            activities.say_hello_sync,
            activities.get_workflow_args,
        ]
