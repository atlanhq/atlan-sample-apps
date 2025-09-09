from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import ExtractorActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

logger = get_logger(__name__)
workflow.logger = logger


@workflow.defn
class ExtractorWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        Orchestrate the table metadata extraction flow:

        1. Read workflow args (supports input_file, output_file with defaults)
        2. Extract and transform table metadata via activities
        3. Log the extraction summary

        Args:
            workflow_config (Dict[str, Any]): Workflow configuration from the server.
        """
        activities_instance = ExtractorActivities()

        # Merge any provided args (from frontend POST body or server config)
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Extract and transform the table metadata directly
        extraction_result: Dict[str, Any] = await workflow.execute_activity(
            activities_instance.extract_table_metadata,
            workflow_args,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Emit the result to logs; UI can be checked via Temporal Web
        if extraction_result.get("status") == "success":
            logger.info(f"Extraction completed successfully: {extraction_result.get('transformed_records', 0)} records processed")
            logger.info(f"Input file: {extraction_result.get('input_file')}")
            logger.info(f"Output file: {extraction_result.get('output_file')}")
        else:
            logger.error(f"Extraction failed: {extraction_result.get('error', 'Unknown error')}")

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """
        Declare which activity methods are part of this workflow for the worker.
        """
        if not isinstance(activities, ExtractorActivities):
            raise TypeError("Activities must be an instance of ExtractorActivities")

        return [
            activities.get_workflow_args,
            activities.extract_table_metadata,
            activities.test_extractor_connectivity,
            activities.perform_preflight_check,
        ]
