from atlan_helpers import get_atlan_client
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity
from pyatlan.model.enums import AtlanWorkflowPhase
import os
from datetime import datetime

logger = get_logger(__name__)
activity.logger = logger


class WorkflowsObservabilityActivities(ActivitiesInterface):
    @activity.defn
    async def fetch_workflows_run(self, args: tuple[str, str]) -> dict:
        """
        Fetch workflow runs from Atlan within a time range, based on a selected date and output type.
        If output_type is 'Local', the workflow run results are stored as JSON files under /tmp/workflows.

        Args:
            args (tuple[str, str]): A tuple containing:
                - selected_date (str): A date string in 'YYYY-MM-DD' format to calculate the time range.
                - output_type (str): Type of output, e.g. 'Local'.

        Returns:
            dict: Not used, but required by Temporal activities API.

        Raises:
            Exception: If fetching or processing workflows fails.
        """
        try:
            selected_date, output_type = args

            if output_type == "Local":
                local_directory = "/tmp/workflows"
                os.makedirs(local_directory, exist_ok=True)

            logger.info(f"Fetching Atlan workflows since: {selected_date}")

            input_date = datetime.strptime(selected_date, "%Y-%m-%d")
            current_datetime = datetime.now()
            time_difference = current_datetime - input_date
            difference_in_hours = int(time_difference.total_seconds() / 3600)

            client = get_atlan_client()

            results = client.workflow.find_runs_by_status_and_time_range(
                status=[AtlanWorkflowPhase.SUCCESS, AtlanWorkflowPhase.FAILED],
                started_at=f"now-{difference_in_hours}h",
            )

            for result in results:
                if output_type == "Local":
                    save_result_locally(result, local_directory)

        except Exception as e:
            logger.error(f"Failed to process workflows: {str(e)}", exc_info=e)
            raise


def save_result_locally(result, local_directory: str) -> None:
    """
    Save a workflow run result to a local directory, structured by date and status.

    Args:
        result: The workflow result object returned by the Atlan client.
        local_directory (str): Base path where files will be saved.

    Raises:
        OSError: If directories or file writing fails.
    """
    try:
        date_str = result.source.status.startedAt[:10]
        subdirs = [date_str, f"{date_str}/SUCCESS", f"{date_str}/FAILED"]

        for subdir in subdirs:
            os.makedirs(os.path.join(local_directory, subdir), exist_ok=True)

        status_dir = "SUCCESS" if result.status == AtlanWorkflowPhase.SUCCESS else "FAILED"
        output_path = os.path.join(local_directory, date_str, status_dir, result.id + ".json")

        with open(output_path, "w") as f:
            f.write(result.json(by_alias=True, exclude_none=True))

        logger.info(f"Saved result to {output_path}")

    except Exception as e:
        logger.error(f"Error saving workflow result locally: {str(e)}", exc_info=e)
        raise
