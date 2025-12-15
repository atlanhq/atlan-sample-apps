import json
import os

import httpx
from app.models import UploadDataInput
from application_sdk.activities.common.utils import (
    build_output_path,
    get_object_store_prefix,
)
from application_sdk.constants import TEMPORARY_PATH
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.services import ObjectStore
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

logger = get_logger(__name__)


def create_local_directory() -> str:
    """
    Creates a local directory if it does not already exist.

    Returns the path to the created or existing local directory.

    Returns:
        The path to the local directory as a string.
    """
    local_directory = f"{TEMPORARY_PATH}{build_output_path()}"
    if os.path.exists(local_directory):
        logger.info(f"Local directory {local_directory} already exists.")
    else:
        logger.info(f"Local directory {local_directory} does not exist.")
    os.makedirs(local_directory, exist_ok=True)
    logger.info(f"local directory created: {local_directory}")
    return local_directory


def save_result_locally(result: UploadDataInput, local_directory: str) -> str:
    """
    Saves the workflow result data as a JSON file in the specified local directory.

    Returns the path to the saved file.

    Args:
        result: The workflow result data to be saved.
        local_directory: The directory where the file will be saved.

    Returns:
        The path to the saved JSON file as a string.
    """
    try:
        output_path = os.path.join(local_directory, f"data_{result.offset}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result.assets_data, f, ensure_ascii=False, indent=4)

        logger.info(f"Saved result to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error saving workflow result locally: {str(e)}", exc_info=e)
        raise e


async def save_result_object_storage(source_file: str) -> None:
    """
    Uploads a local file to object storage for workflow results.

    The file is uploaded to a destination path based on its local path.

    Args:
        source_file: The path to the local file to upload.

    Returns:
        None.
    """
    try:
        destination = get_object_store_prefix(source_file)
        await ObjectStore.upload_file(
            source=source_file,
            destination=destination,
            retain_local_copy=True,
        )
        logger.info(f"{source_file} pushed to object storage {destination}.")

    except Exception as e:
        logger.error(
            f"Error saving workflow result on object storage: {str(e)}", exc_info=e
        )
        raise e


async def download_files(local_directory: str):
    """
    Downloads all files for a workflow from object storage to a local directory.

    The files are downloaded and stored in the specified local directory.

    Args:
        local_directory: The directory where files will be downloaded.

    Returns:
        None.
    """
    try:
        source = get_object_store_prefix(local_directory)
        logger.info(f"Downloading files from {source} to {local_directory}")
        await ObjectStore.download_prefix(source, TEMPORARY_PATH)
        logger.info(f"{source} downloaded to {local_directory}")
    except Exception as e:
        logger.error(
            f"Error downloading workflow result from object storage: {str(e)}",
            exc_info=e,
        )
        raise e


def concatenate_files(local_directory: str) -> str:
    """
    Concatenates all JSON files in a local directory into a single results file.

    Reads each JSON file, combines their contents, and writes the result to 'results.json' in the same directory.

    Args:
        local_directory: The directory containing the JSON files to concatenate.

    Returns:
        The path to the concatenated results file as a string.
    """
    concatenated_content = []
    for filename in os.listdir(local_directory):
        full_filepath = os.path.join(local_directory, filename)
        if not full_filepath.endswith(".json"):
            logger.info(f"Skipping file extraneous file {full_filepath}")
        with open(full_filepath, "r", encoding="utf-8") as infile:
            concatenated_content.extend(json.load(infile))
    output_filename = f"{local_directory}/results.json"
    with open(output_filename, "w", encoding="utf-8") as outfile:
        json.dump(concatenated_content, outfile, indent=4)
    logger.info(f"Concatenated content written to {output_filename}")
    return output_filename


async def post_to_slack(
    client: AsyncWebClient, file_path: str, count_of_assets_without_description: int
) -> None:
    """
    Sends a Slack message and uploads a file to a user about assets missing descriptions.

    Looks up the user by email, sends a reminder message, and attaches a file listing assets without descriptions.

    Args:
        client: The asynchronous Slack WebClient instance.
        file_path: The path to the file to upload.
        count_of_assets_without_description: The number of assets missing descriptions.

    Returns:
        None.
    """
    try:
        email_to_find = os.getenv("SLACK_USER_EMAIL")
        response = await client.users_lookupByEmail(email=email_to_find)
        if user := response.get("user"):
            slack_user = {
                "id": user["id"],
                "name": user.get("name"),
                "real_name": user.get("real_name"),
                "email": user.get("profile", {}).get("email"),
                "display_name": user.get("profile", {}).get("display_name"),
            }
            header = f"Hello {slack_user.get('real_name', slack_user['name'])}! 👋\n\n"
            header += f"I noticed that {count_of_assets_without_description} of your assets are missing a description."
            footer = """Adding a description helps other team members understand what this asset is used for and makes it easier to discover and use.

Could you please add a description when you get a chance? Thanks! 🙏

_This is an automated reminder from the Asset Description Monitor._"""
            message = header + "\n\n" + footer
            response = await client.chat_postMessage(
                channel=slack_user["id"],
                text=message.strip(),
                username="Asset Description Monitor",
                icon_emoji=":memo:",
            )
            logger.info("Message posted.")
            channel = response.data["channel"]
            response_url = await client.files_getUploadURLExternal(
                filename=os.path.basename(file_path), length=os.path.getsize(file_path)
            )
            upload_url = response_url["upload_url"]
            file_id = response_url["file_id"]
            with open(file_path, "rb") as f:
                httpx.post(upload_url, files={"file": f})
            await client.files_completeUploadExternal(
                files=[{"id": file_id, "title": os.path.basename(file_path)}],
                channel_id=channel,
                initial_comment="Attached is a file containing a list of the assets without a description.",
            )
            logger.info("Uploaded file.")
    except SlackApiError as e:
        logger.error(f"Slack API error: {str(e)}")
