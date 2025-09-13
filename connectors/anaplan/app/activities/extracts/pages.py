import asyncio
from typing import Any, Dict, List, Set

from app.clients import AppClient
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


async def extract_pages_data(client: AppClient) -> List[Dict[str, Any]]:
    """Extract basic pages data from Anaplan.

    Fetches all available pages from Anaplan's springboard definition service
    with pagination support, sorted by last accessed date.

    Args:
        client: AppClient instance for API operations.

    Returns:
        List[Dict[str, Any]]: List of page data dictionaries.

    Raises:
        ValueError: If API request fails or no response is received.

    Note:
        URL: https://{host}/a/springboard-definition-service/pages
        Results are sorted by lastAccessed in descending order.
    """
    try:
        logger.info("Starting pages data extraction from Anaplan API")

        # page data dict
        page_data: List[Dict[str, Any]] = []

        # Extract page assets from Anaplan with pagination
        url = f"https://{client.host}/a/springboard-definition-service/pages"
        limit = 100
        offset = 0

        # Paginate through all pages and collect directly in page_data
        while True:
            params = {
                "limit": limit,
                "offset": offset,
                "sort": "lastAccessed",
                "order": "desc",
                "includeReportPages": True,
            }

            response = await client.execute_http_get_request(url, params=params)

            if response is None:
                logger.error("Failed to extract pages data: No response received")
                raise ValueError("Failed to extract pages data: No response received")

            if not response.is_success:
                raise ValueError(f"Failed to fetch pages: {response.status_code}")

            response_dict = response.json()

            if not response_dict.get("items", []):
                break  # No more pages to fetch

            page_data.extend(response_dict.get("items", []))

            offset += limit

        logger.info(
            f"Successfully extracted {len(page_data)} basic pages from Anaplan API"
        )
        return page_data

    except Exception as e:
        logger.error(f"Error extracting pages data: {str(e)}")
        raise


async def get_page_details(
    client: AppClient, page: Dict[str, Any]
) -> Dict[str, Any]:
    """Get detailed information for a single page.

    Fetches additional details for a specific page from Anaplan's API
    and merges them with the basic page information.

    Args:
        client: AppClient instance for API operations.
        page: Dictionary containing basic page information.

    Returns:
        Dict[str, Any]: Enhanced page data with detailed information.

    Note:
        URL: https://{host}/a/springboard-definition-service/{pageType}s/{pageGuid}
        Returns original page data if detailed fetch fails.
    """
    page_type = str(page.get("pageType", "")).lower()
    page_guid = page.get("guid")

    if not page_type or not page_guid:
        return page  # Return basic page data if pageType or guid is missing

    detail_url = f"https://{client.host}/a/springboard-definition-service/{page_type}s/{page_guid}"

    try:
        detail_response = await client.execute_http_get_request(detail_url)

        if detail_response is None:
            logger.warning(
                f"Failed to get detailed info for page {page_guid}: No response received"
            )
            return page  # Return basic page data if no response

        if detail_response.is_success:
            detail_data = detail_response.json()

            # Merge basic page info with detailed info
            detailed_page = {
                **page,  # Include all original page data
                "createdAt": detail_data.get("publishedAt"),
                "updatedAt": detail_data.get("updatedAt"),
                "modelInfos": detail_data.get("modelInfos", []),
                "modelCount": detail_data.get("modelCount"),
            }
            return detailed_page
        else:
            logger.warning(
                f"Failed to get detailed info for page {page_guid}: {detail_response.status_code}"
            )
            return page  # Return basic page data if detailed call fails
    except Exception as detail_error:
        logger.warning(
            f"Error getting detailed info for page {page_guid}: {str(detail_error)}"
        )
        return page  # Return basic page data if detailed call fails


async def extract_pages_with_details(
    client: AppClient,
    valid_app_guids: Set[str],
) -> List[Dict[str, Any]]:
    """Extract pages data with detailed information.

    Orchestrates the extraction of basic page data and enhances each page
    with detailed information from Anaplan's API. Processes pages in chunks
    to prevent event loop overload and enable heartbeats.

    Args:
        client: AppClient instance for API operations.
        valid_app_guids: Set of valid app GUIDs to filter pages by.

    Returns:
        List[Dict[str, Any]]: Pages data with details (no metadata filtering applied).

    Raises:
        Exception: If page extraction or detail fetching fails.

    Note:
        Filters out deleted, archived pages, and pages with invalid app GUIDs.
        Processes pages in chunks of 100 to prevent blocking operations.
    """

    try:
        logger.info("Starting pages extraction with details")

        # Extract basic pages data
        page_data = await extract_pages_data(client)

        # Filter out deleted, archived pages, and pages with invalid app GUIDs
        valid_pages = [
            page
            for page in page_data
            if page.get("deletedAt") is None
            and not page.get("isArchived", False)
            and page.get("appGuid") in valid_app_guids
        ]

        if not valid_pages:
            logger.warning(
                "No valid pages found after filtering deleted, archived pages, and pages with invalid app GUIDs"
            )
            return []
        else:
            logger.info(
                f"Processing {len(valid_pages)} valid pages (after filtering deleted, archived, and invalid app GUID pages) for detailed information"
            )

        # Process all extracted pages [in chunks to prevent blocking calls and enable heartbeats]
        all_detailed_pages = []
        chunk_size = 100
        total_chunks = (len(valid_pages) + chunk_size - 1) // chunk_size

        logger.info(
            f"Starting chunked page detail extraction: {len(valid_pages)} pages in {total_chunks} chunks of {chunk_size} size"
        )

        # Process in chunks to prevent event loop overload and enable heartbeats
        for chunk_index in range(0, len(valid_pages), chunk_size):
            chunk = valid_pages[chunk_index : chunk_index + chunk_size]
            current_chunk = (chunk_index // chunk_size) + 1

            logger.info(
                f"Processing chunk {current_chunk}/{total_chunks}: {len(chunk)} pages"
            )

            # Create tasks for this chunk
            chunk_tasks = []
            for page in chunk:
                task = get_page_details(client, page)
                chunk_tasks.append(task)

            # Execute chunk concurrently
            chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)

            # Process chunk results and handle exceptions
            chunk_pages = 0
            for i, result in enumerate(chunk_results):
                page_guid = chunk[i].get("guid", "unknown")
                if isinstance(result, Exception):
                    logger.error(
                        f"Exception processing page {page_guid}: {str(result)}"
                    )
                    all_detailed_pages.append(chunk[i])  # Use basic page data
                elif isinstance(result, dict):
                    all_detailed_pages.append(result)
                    chunk_pages += 1
                else:
                    logger.warning(
                        f"Unexpected result type for page {page_guid}: {type(result)}"
                    )
                    all_detailed_pages.append(chunk[i])  # Use basic page data

            logger.info(
                f"Chunk {current_chunk}/{total_chunks} completed: {chunk_pages} pages processed"
            )

        logger.info(
            f"Successfully processed {len(all_detailed_pages)} pages with detailed information"
        )
        return all_detailed_pages

    except Exception as e:
        logger.error(f"Error extracting pages with details: {str(e)}")
        raise
