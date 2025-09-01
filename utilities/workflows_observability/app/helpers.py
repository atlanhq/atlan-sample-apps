import os

from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.services import ObjectStore
from pyatlan.model.enums import AtlanWorkflowPhase
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


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

        status_dir = (
            "SUCCESS" if result.status == AtlanWorkflowPhase.SUCCESS else "FAILED"
        )
        output_path = os.path.join(
            local_directory, date_str, status_dir, f"{result.id}.json"
        )

        with open(output_path, "w") as f:
            f.write(result.json(by_alias=True, exclude_none=True))

        logger.info(f"Saved result to {output_path}")

    except Exception as e:
        logger.error(f"Error saving workflow result locally: {str(e)}", exc_info=e)
        raise e


async def save_result_object_storage(output_prefix: str, local_directory: str) -> None:
    """
    Uploads the contents of a local directory to an object storage location under a specified prefix.

    This function is typically used to persist the results of a workflow run by saving files
    from a local path to a remote object store (e.g., S3, GCS), using the provided output prefix
    as the destination path.

    Args:
        output_prefix (str): The prefix path under which the files will be stored in object storage.
        local_directory (str): The local directory containing files to be uploaded.

    Raises:
        OSError: If there is an issue accessing the local directory or files.
        Exception: For any other errors during the upload process.
    """
    try:
        await ObjectStore.upload_prefix(
            destination=output_prefix, source=local_directory
        )
        logger.info("Files pushed to object storage.")

    except Exception as e:
        logger.error(
            f"Error saving workflow result on object storage: {str(e)}", exc_info=e
        )
        raise e
