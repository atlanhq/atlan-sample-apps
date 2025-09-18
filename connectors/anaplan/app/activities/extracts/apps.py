from typing import Any, Dict, List

from app.clients import AppClient
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


async def extract_apps_data(client: AppClient) -> List[Dict[str, Any]]:
    """Extract all apps data from Anaplan.

    Fetches all available apps from Anaplan's springboard definition service
    with pagination support and filters out deleted apps.

    Args:
        client: AppClient instance for API operations.

    Returns:
        List[Dict[str, Any]]: List of active app data dictionaries.

    Raises:
        ValueError: If API request fails or no response is received.

    Note:
        URL: https://{host}/a/springboard-definition-service/apps
        Automatically filters out apps with deletedAt timestamp.
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
        active_app_data = [app for app in app_data if app.get("deletedAt") is None]

        logger.info(
            f"Successfully extracted {len(active_app_data)} active apps from {len(app_data)} total apps"
        )
        return active_app_data

    except Exception as e:
        logger.error(f"Error extracting apps data: {str(e)}")
        raise
