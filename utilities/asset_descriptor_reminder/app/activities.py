from typing import Any, Dict, List

from app.client import AssetDescriptionClient
from app.helper import (
    concatenate_files,
    create_local_directory,
    download_and_concatenate_files,
    post_to_slack,
    save_result_locally,
    save_result_object_storage,
)
from app.models import FetchUserAssetsInput, SendSlackReminderInput, UploadDataInput
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from pyatlan.model.assets import Asset
from pyatlan.model.fluent_search import FluentSearch
from temporalio import activity

logger = get_logger(__name__)


class AssetDescriptionReminderActivities(ActivitiesInterface):
    def __init__(self):
        super().__init__()
        self.client = None

    async def _get_client(self, config: Dict[str, str]) -> AssetDescriptionClient:
        """Get or create a client with config."""
        if not self.client:
            self.client = AssetDescriptionClient()
            await self.client.load(config)
        return self.client

    @activity.defn
    async def fetch_user_assets(
        self, input: FetchUserAssetsInput
    ) -> List[Dict[str, Any]]:
        """
        Fetches assets owned by a specific user from Atlan.
        Returns a list of asset metadata dictionaries for the given user and page parameters.

        Args:
            input: The input containing user username, config, page size, and start index.

        Returns:
            A list of dictionaries, each representing an asset's metadata.
        """
        client = await self._get_client(input.config)
        atlan_client = await client.get_atlan_client()
        user_username = input.user_username
        page_size = input.page_size
        start = input.start

        logger.info(
            f"Fetching assets owned by user: {user_username}, page size: {page_size}"
        )
        try:
            logger.info("Create search query")
            search_request = (
                FluentSearch()
                .select()
                .where(Asset.TYPE_NAME.within(["Table", "View", "Database"]))
                .where(Asset.OWNER_USERS.eq(user_username))
                .include_on_results(Asset.QUALIFIED_NAME)
                .include_on_results(Asset.NAME)
                .include_on_results(Asset.DESCRIPTION)
                .include_on_results(Asset.OWNER_USERS)
                .include_on_results(Asset.USER_DESCRIPTION)
                .page_size(page_size)
                .to_request()
            )
            logger.info("created search")
            # Start retrieving results at the given start
            search_request.dsl.from_ = start
            search_results = await atlan_client.asset.search(search_request)
            logger.info(f"found {search_results.count} assets")

            assets_data = []
            count = 0
            for asset in search_results.current_page():
                count += 1
                asset_info = {
                    "qualified_name": asset.qualified_name,
                    "name": asset.name,
                    "description": asset.description,
                    "user_description": asset.user_description,
                    "owner_users": asset.owner_users,
                    "guid": asset.guid,
                    "type_name": asset.type_name,
                }
                assets_data.append(asset_info)
                logger.debug(
                    f"Found asset: {asset_info['name']} - Description: {bool(asset_info['description'] or asset_info['user_description'])}"
                )
            logger.info(f"Total additional assets processed: {count}")
            return assets_data
        except Exception as e:
            logger.error(f"Error searching for user assets: {str(e)}")
            return []

    @activity.defn
    def find_asset_without_description(
        self, assets_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identifies assets that do not have a description or user description.

        Returns a list of assets missing both description and user description fields.

        Args:
            assets_data: A list of asset metadata dictionaries.

        Returns:
            A list of asset dictionaries without any description.
        """
        without_description_assets = []
        for asset in assets_data:
            description = (asset.get("description") or "").strip()
            user_description = (asset.get("user_description") or "").strip()
            if not description and not user_description:
                logger.info(f"Found asset without description: {asset['name']}")
                without_description_assets.append(asset)
        return without_description_assets

    @activity.defn
    async def upload_data(self, input: UploadDataInput):
        """
        Uploads workflow data to local storage and then to object storage.

        Saves the result locally and then uploads the saved file to object storage.

        Args:
            input: The input containing workflow ID and result data.

        Returns:
            None.
        """
        local_directory = create_local_directory(input.workflow_id)
        source_file = save_result_locally(result=input, local_directory=local_directory)
        await save_result_object_storage(source_file=source_file)

    @activity.defn
    async def send_slack_reminder(self, input: SendSlackReminderInput):
        """
        Sends a Slack reminder with information about assets missing descriptions.

        Downloads and concatenates result files, then posts a message to Slack with the relevant asset information.

        Args:
            input: The input containing workflow ID, configuration, and asset count.

        """
        try:
            local_directory = create_local_directory(input.workflow_id)
            await download_and_concatenate_files(
                workflow_id=input.workflow_id, local_directory=local_directory
            )
            output_files = concatenate_files(local_directory=local_directory)

            client = await self._get_client(input.config)
            slack_client = await client.get_slack_client()
            await post_to_slack(
                slack_client,
                output_files,
                count_of_assets_without_description=input.count_of_assets_without_description,
            )
        except Exception as e:
            logger.error(f"❌ Error sending Slack message: {e}")
            return {"success": False, "error": str(e)}
