from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class FetchUserAssetsInput:
    """
    Represents the input parameters required to fetch assets for a specific user.

    Stores configuration, user information, and pagination details for asset retrieval.

    Attributes:
        config: Configuration dictionary for the client.
        user_username: The username of the user whose assets are being fetched.
        page_size: Number of assets to fetch per page.
        start: The starting index for pagination.
        asset_limit: The maximum number of assets to fetch.
    """

    config: Dict[str, str]
    user_username: str
    page_size: int = 300
    start: int = 0
    asset_limit: int = 50

    def increment_start(self):
        self.start += self.page_size


@dataclass
class UploadDataInput:
    """
    Represents the input data required for uploading workflow results.

    Contains asset data, workflow identifier, and offset for file naming or pagination.

    Attributes:
        assets_data: A list of dictionaries containing asset metadata.
        offset: The offset used for file naming or pagination.
    """

    assets_data: List[Dict[str, Any]]
    offset: int


@dataclass
class SendSlackReminderInput:
    """
    Represents the input data required to send a Slack reminder about assets.

    Contains workflow ID, configuration, and the count of assets missing descriptions.

    Attributes:
        config: Configuration dictionary for the client.
        count_of_assets_without_description: The number of assets without descriptions.
    """

    config: Dict[str, str]
    count_of_assets_without_description: int
