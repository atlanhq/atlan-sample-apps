from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from activities import AIGiphyActivities
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

        # Get the input string from workflow_args. Provide a default if not found.
        ai_input_string: str = workflow_args.get(
            "ai_input_string", "Fetch a cat gif and send it to test@example.com"
        )

        logger.info(f"Starting AI Giphy workflow with input: {ai_input_string}")

        # Execute the AI agent activity
        agent_output = await workflow.execute_activity(
            activities_instance.run_ai_agent,
            ai_input_string,
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
