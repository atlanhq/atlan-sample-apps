from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from application_sdk.activities import ActivitiesInterface
from application_sdk.common.logger_adaptors import get_logger
from application_sdk.inputs.statestore import StateStoreInput
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

from activities import AIGiphyActivities

workflow.logger = get_logger(__name__)


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
        workflow_id = workflow_config["workflow_id"]
        # Extract workflow arguments using StateStoreInput
        # This assumes the input string for the AI agent is stored under a key, e.g., "ai_input_string"
        workflow_args: Dict[str, Any] = StateStoreInput.extract_configuration(
            workflow_id
        )

        activities_instance = AIGiphyActivities()

        # Get the input string from workflow_args. Provide a default if not found.
        ai_input_string: str = workflow_args.get("ai_input_string", "Fetch a cat gif and send it to test@example.com")

        workflow.logger.info(f"Starting AI Giphy workflow with input: {ai_input_string}")

        # Execute the AI agent activity
        agent_output = await workflow.execute_activity(
            activities_instance.run_ai_agent,
            ai_input_string,
            start_to_close_timeout=timedelta(seconds=60),  # Increased timeout for potentially longer AI tasks
        )

        workflow.logger.info(f"AI Agent activity completed. Output: {agent_output}")
        workflow.logger.info("AI Giphy workflow completed successfully")

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
        ]
