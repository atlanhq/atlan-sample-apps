from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import (
    FetchWorkflowsRunInput,
    SaveResultsLocallyInput,
    SaveResultsObjectInput,
    WorkflowsObservabilityActivities,
)
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
            WorkflowsObservabilityActivities.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        selected_date: str = workflow_args.get(
            "selectedDate", "atlan-snowflake-miner-1743729606"
        )
        output_type: str = workflow_args.get("outputType", "Local")
        output_prefix: str = workflow_args.get("outputPrefix", "")
        workflow.logger.info("Starting workflows observability workflow")

        run_input = FetchWorkflowsRunInput(
            selected_date, output_type, output_prefix, None, size=10
        )
        workflow.logger.info("Creating local directory")
        local_info = await workflow.execute_activity(
            WorkflowsObservabilityActivities.create_local_directory,
            run_input.output_type,
            start_to_close_timeout=timedelta(seconds=10),
        )
        run_input.local_directory = local_info.local_directory
        while True:
            workflow.logger.info(f"run_input: {run_input}")
            results = await workflow.execute_activity(
                WorkflowsObservabilityActivities.fetch_workflows_run,
                run_input,
                start_to_close_timeout=timedelta(seconds=60),
            )
            if len(results) == 0:
                workflow.logger.info(f"no more runs found for {run_input}")
                break
            run_input.start += len(results)
            # This activity needs access to the local directory, previously created
            # so it's run on the same task_queue so it will run on the same machine
            await workflow.execute_activity(
                WorkflowsObservabilityActivities.save_results_locally,
                SaveResultsLocallyInput(
                    local_directory=run_input.local_directory, result=results
                ),
                start_to_close_timeout=timedelta(seconds=3600),
                task_queue=local_info.task_queue,
            )
        if output_type == "Object Storage":
            # This activity needs access to the local directory, previously created
            # so it's run on the same task_queue so it will run on the same machine
            await workflow.execute_activity(
                WorkflowsObservabilityActivities.save_result_object,
                SaveResultsObjectInput(
                    output_prefix=run_input.output_prefix,
                    local_directory=run_input.local_directory,
                ),
                start_to_close_timeout=timedelta(seconds=3600),
                task_queue=local_info.task_queue,
            )

        workflow.logger.info("Workflows observability workflow completed")

    @staticmethod
    def get_activities(
        activities: WorkflowsObservabilityActivities,
    ) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (WorkflowsObservabilityActivities): The activities instance
                containing the workflow observability operations.

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods to be executed
                in order.
        """

        return [
            activities.fetch_workflows_run,
            activities.get_workflow_args,
            activities.create_local_directory,
            activities.save_result_object,
            activities.save_results_locally,
        ]
