import os
from typing import Any, Dict, Set

from application_sdk.io.parquet import ParquetFileReader, ParquetFileWriter
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


def setup_parquet_output(
    workflow_args: Dict[str, Any], output_suffix: str
) -> ParquetFileWriter:
    """Setup parquet output for extract activities.

    Args:
        workflow_args: Dictionary containing output configuration.
        output_suffix: Suffix for the output path (e.g., "raw/app").

    Returns:
        ParquetFileWriter: Configured parquet output instance.

    Raises:
        ValueError: If output path is not provided in workflow_args.
    """

    output_path = workflow_args.get("output_path")

    if not output_path:
        logger.error("Output path not provided in workflow_args.")
        raise ValueError("Output path must be specified in workflow_args.")

    # Create parquet output object
    parquet_output = ParquetFileWriter(
        output_path=output_path,
        output_suffix=output_suffix,
    )

    return parquet_output


async def get_app_guids(workflow_args: Dict[str, Any]) -> Set[str]:
    """Get valid app GUIDs from app parquet files.

    Reads the previously extracted app parquet files to extract all valid
    app GUIDs for filtering pages.

    Args:
        workflow_args: Dictionary containing output configuration.

    Returns:
        Set[str]: Set of valid app GUIDs.

    Raises:
        ValueError: If output path is not provided in workflow_args.
    """

    output_path = workflow_args.get("output_path")

    if not output_path:
        raise ValueError("Output path must be specified in workflow_args")

    # Read app parquet files to get valid app GUIDs
    app_parquet_input = ParquetFileReader(
        path=os.path.join(output_path, "raw", "app"),
    )
    app_parquet_input = app_parquet_input.get_batched_daft_dataframe()

    # Create set of valid app GUIDs from app extracts
    all_apps: set = set()
    async for app_dataframe in app_parquet_input:
        if app_dataframe is not None and app_dataframe.count_rows() > 0:
            app_list = app_dataframe.to_pylist()
            guids = [item["guid"] for item in app_list if item["guid"] is not None]
            all_apps.update(guids)

    logger.info(f"Found {len(all_apps)} valid app GUIDs from app extracts")
    return all_apps


def should_include_asset(
    asset_data: Dict[str, Any],
    typename: str,
    metadata_filter_state: str,
    metadata_filter: Dict[str, Any],
) -> bool:
    """Determine if an asset should be included based on metadata filter state.

    Applies include/exclude filtering logic based on the current filter state
    and configuration for different asset types.

    Args:
        asset_data: Dictionary containing asset information.
        typename: Type of asset (e.g., "app", "page").
        metadata_filter_state: Current filter state ("include", "exclude", or "none").
        metadata_filter: Dictionary containing filter configuration.

    Returns:
        bool: True if asset should be included, False otherwise.

    Note:
        For apps: Uses "guid" field as identifier.
        For pages: Uses "appGuid" and "guid" fields as identifiers.
        Returns True in case of errors to avoid data loss.
    """

    try:
        # If filter state is "none", include all assets
        if metadata_filter_state == "none":
            return True

        # If filter is empty, include all assets
        if not metadata_filter:
            return True

        # Handle different asset types
        if typename == "app":
            # For apps, use the "guid" field as the asset identifier
            app_id = asset_data.get("guid")
            if not app_id:
                logger.warning(f"App asset missing 'guid' field: {asset_data}")
                return False

            if metadata_filter_state == "include":
                # Include only if workspace ID is in the filter
                return app_id in metadata_filter
            elif metadata_filter_state == "exclude":
                # Exclude if workspace ID is in the filter
                return app_id not in metadata_filter
            else:
                logger.warning(
                    f"Unknown metadata filter state: {metadata_filter_state}"
                )
                return True

        elif typename == "page":
            # For pages, use the "appGuid" and "guid" field as the asset identifier
            app_id = asset_data.get("appGuid")
            page_id = asset_data.get("guid")
            if not app_id or not page_id:
                logger.warning(
                    f"Page asset missing 'appGuid' or 'guid' field: {asset_data}"
                )
                return False

            # when app id is in the filter and either has page ids with this one included or is empty completely, include the page
            if metadata_filter_state == "include":
                if app_id in metadata_filter:
                    if not metadata_filter[app_id]:
                        return True
                    else:
                        return page_id in metadata_filter[app_id]
                else:
                    return False
            elif metadata_filter_state == "exclude":
                if app_id in metadata_filter:
                    if not metadata_filter[app_id]:
                        return False
                    else:
                        return page_id not in metadata_filter[app_id]
                else:
                    return True
            else:
                logger.warning(
                    f"Unknown metadata filter state: {metadata_filter_state}"
                )
                return True

        logger.debug(
            f"No specific filter handling for typename '{typename}', including asset"
        )
        return True

    except Exception as e:
        logger.error(f"Error in should_include_asset for {typename}: {str(e)}")
        # In case of error, include the asset to avoid data loss
        return True
