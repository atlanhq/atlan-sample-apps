from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

# Import GiphyActivities outside of the workflow code
from app.activities import GiphyActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

logger = get_logger(__name__)
workflow.logger = logger


@workflow.defn
class GiphyWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        This workflow is used to send a GIF to a list of recipients.

        Args:
            workflow_config (Dict[str, Any]): The workflow configuration

        Returns:
            None
        """
        activities_instance = GiphyActivities()

        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        search_term: str = workflow_args.get("search_term", "funny cat")
        recipients: str = workflow_args.get("recipients")  # pyright: ignore[reportAssignmentType]

        # Step 1: Fetch the GIF
        gif_url = await workflow.execute_activity(
            activities_instance.fetch_gif,
            search_term,
            start_to_close_timeout=timedelta(seconds=10),
        )
        logger.info(f"Fetched GIF: {gif_url}")

        # Step 2: Send the email with the GIF
        await workflow.execute_activity(
            activities_instance.send_email,
            {"recipients": recipients, "gif_url": gif_url},
            start_to_close_timeout=timedelta(seconds=10),
        )

        logger.info("Giphy workflow completed")

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
        if not isinstance(activities, GiphyActivities):
            raise TypeError("Activities must be an instance of HelloWorldActivities")

        return [
            activities.fetch_gif,
            activities.send_email,
            activities.get_workflow_args,
        ]
