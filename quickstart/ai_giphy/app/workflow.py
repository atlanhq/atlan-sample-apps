from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import AIGiphyActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

logger = get_logger(__name__)
workflow.logger = logger


@workflow.defn
class AIGiphyWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        This workflow runs an AI agent based on the input string.

        Args:
            workflow_config (Dict[str, Any]): The workflow configuration,
                                             expected to contain 'workflow_id'.

        Returns:
            None
        """
        activities_instance = AIGiphyActivities()

        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if workflow_config:
            workflow_args.update(workflow_config)
            logger.info(f"Merged workflow_args: {workflow_args}")

        # Get the input string from workflow_args. Provide a default if not found.
        ai_input_string: str = workflow_args.get(
            "ai_input_string", "Fetch a cat gif and send it to test@example.com"
        )
        giphy_api_key: str = workflow_args.get("giphy_api_key")
        smtp_host: str = workflow_args.get("smtp_host")
        smtp_port: int = workflow_args.get("smtp_port")
        smtp_username: str = workflow_args.get("smtp_username")
        smtp_password: str = workflow_args.get("smtp_password")
        smtp_sender: str = workflow_args.get("smtp_sender")
        openai_api_key: str = workflow_args.get("openai_api_key")
        openai_model_name: str = workflow_args.get("openai_model_name")
        openai_base_url: str = workflow_args.get("openai_base_url")

        logger.info(f"Starting AI Giphy workflow with input: {ai_input_string}")

        # Prepare config dict with all configuration values
        agent_config = {
            "ai_input_string": ai_input_string,
            "giphy_api_key": giphy_api_key,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "smtp_username": smtp_username,
            "smtp_password": smtp_password,
            "smtp_sender": smtp_sender,
            "openai_api_key": openai_api_key,
            "openai_model_name": openai_model_name,
            "openai_base_url": openai_base_url,
        }

        # Execute the AI agent activity
        agent_output = await workflow.execute_activity(
            activities_instance.run_ai_agent,
            agent_config,
            start_to_close_timeout=timedelta(
                seconds=60
            ),  # Increased timeout for potentially longer AI tasks
        )

        logger.info(f"AI Agent activity completed. Output: {agent_output}")

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (ActivitiesInterface): The activities instance.

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods.
        """
        if not isinstance(activities, AIGiphyActivities):
            raise TypeError("Activities must be an instance of AIGiphyActivities")

        return [
            activities.run_ai_agent,
            activities.get_workflow_args,
        ]
