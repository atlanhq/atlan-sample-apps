import os
from datetime import datetime

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from app.helpers import get_atlan_client, save_result_locally, save_result_object_storage
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class WorkflowsObservabilityActivities(ActivitiesInterface):
    @activity.defn
    async def fetch_workflows_run(self, args: tuple[str, str, str]) -> dict:
        """
        Fetch workflow runs from Atlan within a time range, based on a selected date and output type.
        If output_type is 'Local', the workflow run results are stored as JSON files under /tmp/workflows.

        Args:
            args (tuple[str, str]): A tuple containing:
                - selected_date (str): A date string in 'YYYY-MM-DD' format to calculate the time range.
                - output_type (str): Type of output, e.g. 'Local'.
                - output_prefix (str): The directory path or prefix under which extracted data will be stored in the object storage.

        Returns:
            dict: Not used, but required by Temporal activities API.

        Raises:
            Exception: If fetching or processing workflows fails.
        """
        try:
            selected_date, output_type, output_prefix = args

            if output_type == "Local":
                local_directory = "./local/workflows"
            elif output_type == "Object Storage":
                local_directory = output_prefix
            os.makedirs(local_directory, exist_ok=True)

            logger.info(f"Fetching Atlan workflows since: {selected_date}")

            input_date = datetime.strptime(selected_date, "%Y-%m-%d")
            current_datetime = datetime.now()
            time_difference = current_datetime - input_date
            difference_in_hours = int(time_difference.total_seconds() / 3600)

            client = get_atlan_client()
            from pyatlan.model.enums import AtlanWorkflowPhase

            results = client.workflow.find_runs_by_status_and_time_range(
                status=[AtlanWorkflowPhase.SUCCESS, AtlanWorkflowPhase.FAILED],
                started_at=f"now-{difference_in_hours}h",
            )

            for result in results:
                save_result_locally(result, local_directory)

            if output_type == "Object Storage":
                await save_result_object_storage("", local_directory)

        except Exception as e:
            logger.error(f"Failed to process workflows: {str(e)}", exc_info=e)
            raise e
