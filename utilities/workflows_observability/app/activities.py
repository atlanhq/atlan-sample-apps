import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.helpers import save_result_locally, save_result_object_storage
from application_sdk.activities import ActivitiesInterface
from application_sdk.clients.atlan import get_async_client
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


@dataclass
class LocalInfo:
    """
    Stores information about a local directory and associated task queue.

    This dataclass is the output of the create_local_directory function.

    Attributes:
        local_directory (str): The path to the local directory.
        task_queue (str): The name of the task queue associated with the activity.
    """

    local_directory: str
    task_queue: str


@dataclass
class SaveResultsLocallyInput:
    """
    Represents the input required to save workflow results locally.

    This dataclass contains the local directory path and a list of results to be saved.

    Attributes:
        local_directory (str): The path to the local directory where results will be saved.
        result (list[str]): A list of workflow results to be saved locally.
    """

    local_directory: str
    result: list[str]


@dataclass
class SaveResultsObjectInput:
    """
    Represents the input required to save workflow results to object storage.

    This dataclass contains the output prefix and the local directory path for uploading results.

    Attributes:
        output_prefix (str): The prefix or path in the object storage where results will be uploaded.
        local_directory (str): The path to the local directory containing results to be uploaded.
    """

    output_prefix: str
    local_directory: str


@dataclass
class FetchWorkflowsRunInput:
    """
    Represents the input parameters for fetching workflow runs from Atlan.

    This dataclass contains date, output type, output prefix, and pagination information for workflow queries.

    Attributes:
        selected_date (str): The date from which to fetch workflow runs.
        output_type (str): The type of output storage.
        output_prefix (str): The prefix or path for output storage.
        local_directory (Optional[str]): The local directory path, if applicable.
        start (int): The starting index for pagination.
        size (int): The number of results to fetch per page.
    """

    selected_date: str
    output_type: str
    output_prefix: str
    local_directory: Optional[str] = None
    start: int = 0
    size: int = 1


class WorkflowsObservabilityActivities(ActivitiesInterface):
    @activity.defn
    async def dummy(self, parm1: str, parm2: int):
        logger.info(f"parm1: {parm1}")
        logger.info(f"parm1: {parm2}")

    @activity.defn
    async def create_local_directory(self, output_type: str) -> LocalInfo:
        """
        Create a local directory for storing workflow results based on the output type.
        Returns a LocalInfo object containing the directory path and task queue name.
        Subsequent activities need to access the directory created by this activity consequently
        they must run on the same machine so we pass the name of the task queue that this
        activity was run on so it can be used by subsequent activities.

        Args:
            output_type (str): The type of output storage, e.g. 'Local' or 'Object Storage'.

        Returns:
            LocalInfo: An object containing the local directory path and task queue name.
        """
        if output_type == "Local":
            local_directory = "./local/workflows"
        elif output_type == "Object Storage":
            local_directory = input.output_prefix
        os.makedirs(local_directory, exist_ok=True)
        logger.info(f"local directory created: {local_directory}")
        return LocalInfo(
            local_directory=local_directory, task_queue=activity.info().task_queue
        )

    @activity.defn
    async def fetch_workflows_run(self, input: FetchWorkflowsRunInput):
        """
        Fetches a page of workflow runs from Atlan within a specified date range and status.

        Returns a list of workflow run results matching the criteria.

        Args:
            input (FetchWorkflowsRunInput): The input parameters specifying date, output type, and pagination.

        Returns:
            list: A list of workflow run results in JSON format.
        Raises:
            Exception: If fetching or processing workflows fails.
        """
        try:
            logger.info(f"Fetching Atlan workflows since: {input.selected_date}")

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
                return [
                    result.json(by_alias=True, exclude_none=True)
                    for result in results.current_page()
                ]
            else:
                return []
        except Exception as e:
            logger.error(
                f"Failed to retrieve workflow information: {str(e)}", exc_info=e
            )
            raise e

    @activity.defn
    async def save_results_locally(self, input: SaveResultsLocallyInput):
        """
        Saves workflow results to a specified local directory.

        Iterates over the provided results and writes each to the local directory.

        Args:
            input (SaveResultsLocallyInput): The input containing the local directory and results to save.

        Returns:
            None
        """
        logger.info(f"Saving locally to {input.local_directory}")
        for result in input.result:
            save_result_locally(result, input.local_directory)

    @activity.defn
    async def save_result_object(self, input: SaveResultsObjectInput):
        """
        Uploads workflow results from a local directory to object storage.

        Transfers all results found in the specified local directory to the given object storage prefix.

        Args:
            input (SaveResultsObjectInput): The input containing the output prefix and local directory.

        Returns:
            None
        """
        logger.info(f"Uploading to {input.local_directory}")
        await save_result_object_storage(input.output_prefix, input.local_directory)
