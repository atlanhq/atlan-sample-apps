from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import FetchWorkflowsRunInput, WorkflowsObservabilityActivities
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

workflow.logger = get_logger(__name__)


@workflow.defn
class WorkflowsObservabilityWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]):
        """
        Runs the workflows observability workflow to process and store workflow runs.

        This method retrieves workflow configuration, fetches workflow runs in batches,
        and logs the total number of runs processed.

        Args:
            workflow_config (Dict[str, Any]): The configuration dictionary for the workflow.

        """
        # Get the workflow configuration from the state store
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            WorkflowsObservabilityActivities.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info(f"Workflow args: {workflow_args}")
        selected_date: str = workflow_args.get(
            "selectedDate", "atlan-snowflake-miner-1743729606"
        )
        output_prefix: str = workflow_args.get("outputPrefix", "")
        workflow.logger.info(f"Output prefix: {output_prefix}")
        workflow.logger.info("Starting workflows observability workflow")

        run_input = FetchWorkflowsRunInput(
            selected_date=selected_date,
            output_prefix=output_prefix,
            size=10,
        )
        total = 0
        while True:
            workflow.logger.info(f"run_input: {run_input}")
            count = await workflow.execute_activity(
                WorkflowsObservabilityActivities.fetch_and_store_workflows_run_by_page,
                run_input,
                start_to_close_timeout=timedelta(seconds=60),
            )
            workflow.logger.info(f"results: {count}")
            if count == 0:
                workflow.logger.info(f"no more runs found for {run_input}")
                break
            run_input.start += count
            total += count
        workflow.logger.info(f"total runs: {total}")
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
            activities.fetch_and_store_workflows_run_by_page,
            activities.get_workflow_args,
        ]
