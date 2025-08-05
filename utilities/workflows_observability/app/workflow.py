from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

workflow.logger = get_logger(__name__)


@workflow.defn
class WorkflowsObservabilityWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        Entry point for the Workflows Observability Workflow.

        This method orchestrates the observability logic by:
        1. Extracting the workflow configuration from the state store using `get_workflow_args`.
        2. Using the extracted parameters (e.g., date and output type) to query Atlan for
           recent workflow runs via the `fetch_workflows_run` activity.
        3. Logging the start and completion of the workflow execution.

        Args:
            workflow_config (Dict[str, Any]): Dictionary containing metadata and configuration
                used to initialize the workflow. Expected keys include:
                - "selectedDate" (str): The reference date (in 'YYYY-MM-DD') for retrieving workflow runs.
                - "outputType" (str): The target destination for output data (e.g., "Local").
                - "outputPrefix" (str): The directory path or prefix under which extracted data will be stored in the object storage.

        Returns:
            None
        """

        # Get the workflow configuration from the state store
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            "get_workflow_args",
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        selected_date: str = workflow_args.get(
            "selectedDate", "atlan-snowflake-miner-1743729606"
        )
        output_type: str = workflow_args.get("outputType", "Local")
        output_prefix: str = workflow_args.get("outputPrefix", "")
        workflow.logger.info("Starting workflows observability workflow")

        # Process workflow runs
        await workflow.execute_activity(
            "fetch_workflows_run",
            (selected_date, output_type, output_prefix),
            start_to_close_timeout=timedelta(seconds=3600),
        )

        workflow.logger.info("Workflows observability workflow completed")

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (ActivitiesInterface): The activities instance
                containing the workflow observability operations.

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods to be executed
                in order.
        """

        return [
            activities.fetch_workflows_run,
            activities.get_workflow_args,
        ]
