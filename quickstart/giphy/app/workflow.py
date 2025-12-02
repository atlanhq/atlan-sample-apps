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

        if workflow_config:
            workflow_args.update(workflow_config)
            logger.info(f"Merged workflow_args: {workflow_args}")

        search_term: str = workflow_args.get("search_term", "funny cat")
        recipients: str = workflow_args.get("recipients")
        giphy_api_key: str = workflow_args.get("giphy_api_key")
        smtp_host: str = workflow_args.get("smtp_host")
        smtp_port: int = workflow_args.get("smtp_port")
        smtp_username: str = workflow_args.get("smtp_username")
        smtp_password: str = workflow_args.get("smtp_password")
        smtp_sender: str = workflow_args.get("smtp_sender")

        # Step 1: Fetch the GIF
        fetch_config = {
            "search_term": search_term,
            "giphy_api_key": giphy_api_key,
        }
        gif_url = await workflow.execute_activity(
            activities_instance.fetch_gif,
            fetch_config,
            start_to_close_timeout=timedelta(seconds=10),
        )
        logger.info(f"Fetched GIF: {gif_url}")

        # Step 2: Send the email with the GIF
        email_config = {
            "recipients": recipients,
            "gif_url": gif_url,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "smtp_username": smtp_username,
            "smtp_password": smtp_password,
            "smtp_sender": smtp_sender,
        }
        await workflow.execute_activity(
            activities_instance.send_email,
            email_config,
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
