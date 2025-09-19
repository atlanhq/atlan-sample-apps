from dataclasses import dataclass
from datetime import datetime

from app.helpers import (
    create_local_directory,
    save_result_locally,
    save_result_object_storage,
)
from application_sdk.activities import ActivitiesInterface
from application_sdk.clients.atlan import get_async_client
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


@dataclass
class FetchWorkflowsRunInput:
    """
    Represents the input parameters for fetching workflow runs from Atlan.

    This dataclass contains date, output type, output prefix, and pagination information for workflow queries.

    Attributes:
        selected_date (str): The date from which to fetch workflow runs.
        output_type (str): The type of output storage.
        output_prefix (str): The prefix or path for output storage.
        start (int): The starting index for pagination.
        size (int): The number of results to fetch per page.
    """

    selected_date: str
    output_type: str
    output_prefix: str
    start: int = 0
    size: int = 1


class WorkflowsObservabilityActivities(ActivitiesInterface):
    @activity.defn
    async def fetch_and_store_workflows_run_by_page(
        self, input: FetchWorkflowsRunInput
    ) -> int:
        """
        Fetches workflow runs from Atlan and stores their results locally and in object storage.

        This activity retrieves workflow runs based on the provided input parameters, saves each result
        to a local directory, uploads the results to object storage, and returns the number of runs processed.

        Args:
            input (FetchWorkflowsRunInput): The input parameters for fetching workflow runs.

        Returns:
            int: The number of workflow runs processed and stored.

        Raises:
            Exception: If there is an error during fetching, saving, or uploading workflow results.
        """
        try:
            logger.info(f"Fetching Atlan workflows since: {input.selected_date}")
            local_directory = create_local_directory(output_prefix=input.output_prefix)
            input_date = datetime.strptime(input.selected_date, "%Y-%m-%d")
            current_datetime = datetime.now()
            time_difference = current_datetime - input_date
            difference_in_hours = int(time_difference.total_seconds() / 3600)

            client = await get_async_client()
            from pyatlan.model.enums import AtlanWorkflowPhase

            logger.info(f"Fetching workflows started at: {difference_in_hours}")
            results = await client.workflow.find_runs_by_status_and_time_range(
                status=[AtlanWorkflowPhase.SUCCESS, AtlanWorkflowPhase.FAILED],
                started_at=f"now-{difference_in_hours}h",
                size=input.size,
                from_=input.start,
            )
            logger.info(f"the results: {results}")
            if results.hits and results.hits.hits:
                count = 0
                for result in results.current_page():
                    count += 1
                    logger.info(f"count: {count}")
                    save_result_locally(result=result, local_directory=local_directory)
                await save_result_object_storage(
                    output_prefix=input.output_prefix, local_directory=local_directory
                )
                logger.info(f"Total processed results: {count}")
                return count
            else:
                return 0
        except Exception as e:
            logger.error(
                f"Failed to retrieve workflow information: {str(e)}", exc_info=e
            )
            raise e
