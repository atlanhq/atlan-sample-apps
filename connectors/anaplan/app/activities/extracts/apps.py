from typing import Any, Dict, List

from app.activities.utils import should_include_asset
from app.clients import AnaplanApiClient
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


async def extract_apps_data(
    client: AnaplanApiClient,
    metadata_filter_state: str,
    metadata_filter: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Extract apps data from Anaplan.

    ------------------------------------------------------------
    URL: https://{host}/a/springboard-definition-service/apps
    RESPONSE: {
        "items": [
            {
                "guid": "<app_guid>",
                "name": "<app_name>",
                "description": "<app_description>",
                "pages": [],
                "categories": [],
                "landingPages": [],
                "recents": [],
                "customerId": "<customer_id>",
                "deletedAt": <null or timestamp>,
                "mpCount": <number>,
                "isFavorite": <boolean>,
                "isAllArchivedPages": <boolean>,
                "ordering": <null or number>,
                "applicationContainerId": <null or number>
            },....
        ],
        "paging": {
            "offset": <number>,
            "limit": <number>,
            "totalItemCount": <number>
        },
        "customerId": "<customer_id>"
    }
    """
    try:
        logger.info("Starting apps data extraction from Anaplan API")

        # app data dict
        app_data: List[Dict[str, Any]] = []

        # Extract app assets from Anaplan with pagination
        url = f"https://{client.host}/a/springboard-definition-service/apps"
        limit = 100
        offset = 0

        # Paginate through all apps and collect directly in app_data
        while True:
            params = {"limit": limit, "offset": offset}

            response = await client.execute_http_get_request(url, params=params)

            if response is None:
                logger.error("Failed to extract apps data: No response received")
                raise ValueError("Failed to extract apps data: No response received")

            if not response.is_success:
                raise ValueError(f"Failed to fetch apps: {response.status_code}")

            response_dict = response.json()
            app_data.extend(response_dict.get("items", []))

            paging = response_dict.get("paging", {})
            total_size = paging.get("totalItemCount", 0)
            offset += limit

            if offset >= total_size:
                break

        # Filter out deleted apps during extraction
        # NOTE: can become a blocking code if the number of apps is very large and heartbeat is not sent during that time
        filtered_app_data = [
            app
            for app in app_data
            if app.get("deletedAt") is None
            and should_include_asset(
                app, "anaplanapp", metadata_filter_state, metadata_filter
            )
        ]

        logger.info(
            f"Successfully extracted {len(filtered_app_data)} non-deleted apps from {len(app_data)} total apps"
        )
        return filtered_app_data

    except Exception as e:
        logger.error(f"Error extracting apps data: {str(e)}")
        raise
