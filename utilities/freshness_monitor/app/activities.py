import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

from application_sdk.activities import ActivitiesInterface
from application_sdk.clients.atlan import get_async_client
from application_sdk.observability.logger_adaptor import get_logger
from pyatlan.client.aio import AsyncAtlanClient
from pyatlan.model.assets import Asset, Table
from pyatlan.model.core import Announcement
from pyatlan.model.enums import AnnouncementType
from pyatlan.model.fluent_search import FluentSearch
from temporalio import activity

logger = get_logger(__name__)


@dataclass
class FetchTablesMetadataInput:
    """Input data for fetching tables metadata.

    Contains pagination information for retrieving table metadata in batches.
    """

    start: int
    page_size: int

    def increment_start(self):
        """Increment the start index by the page size.

        Updates the start attribute to point to the next page of results.
        """
        self.start += self.page_size


@dataclass
class TagStaleTablesOutput:
    """Represents the output of tagging stale tables.

    Tracks the number of tables successfully tagged and the number of failures.
    """

    tagged_count: int = 0
    failed_count: int = 0


class FreshnessMonitorActivities(ActivitiesInterface):
    def __init__(self):
        super().__init__()
        self.atlan_client = None

    async def _get_atlan_client(self) -> AsyncAtlanClient:
        """Return the initialized Atlan client"""
        if self.atlan_client is None:
            self.atlan_client = await get_async_client()
        return self.atlan_client

    @activity.defn
    async def fetch_tables_metadata(
        self, input: FetchTablesMetadataInput
    ) -> List[Dict[str, Any]]:
        """Activity 1: Fetch table metadata from Atlan"""
        client = await self._get_atlan_client()
        # Build search request for tables
        logger.info("Fetching tables metadata...")
        search_request = (
            FluentSearch()
            .select()
            .where(Asset.TYPE_NAME.eq("Table"))
            .include_on_results(Asset.QUALIFIED_NAME)
            .include_on_results(Asset.NAME)
            .include_on_results(Asset.UPDATE_TIME)
            .include_on_results(Asset.CREATE_TIME)
            .page_size(input.page_size)
            .to_request()
        )
        # Start retrieving results at the given start
        search_request.dsl.from_ = input.start
        search_results = await client.asset.search(search_request)
        tables_data = []
        count = 0
        # Iterate over one page of search results
        for asset in search_results.current_page():
            if isinstance(asset, Table):
                table_info = {
                    "qualified_name": asset.attributes.qualified_name,
                    "name": asset.attributes.name,
                    "update_time": asset.update_time,  # Already a timestamp number
                    "create_time": asset.create_time,  # Already a timestamp number
                    "guid": asset.guid,
                }
                tables_data.append(table_info)
                count += 1
                logger.debug(
                    f"Processed table {input.start + count}: {table_info['name']} {table_info}"
                )

        logger.info(f"Total additional tables processed: {count}")
        return tables_data

    @activity.defn
    def identify_stale_tables(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Activity 2: Filter and identify stale tables based on the threshold days"""
        tables_data = args["tables_data"]
        threshold_days = args["threshold_days"] or os.getenv("THRESHOLD_DAYS")

        stale_tables = []
        threshold_date = datetime.now() - timedelta(days=threshold_days)

        for table in tables_data:
            if update_time := table.get("update_time"):
                # Convert timestamp to datetime if needed
                if isinstance(update_time, (int, float)):
                    update_datetime = datetime.fromtimestamp(
                        update_time / 1000
                    )  # Assuming milliseconds
                else:
                    update_datetime = update_time

                if update_datetime < threshold_date:
                    table["stale_since"] = (
                        threshold_date.isoformat()
                    )  # Convert to ISO string
                    table["days_stale"] = (datetime.now() - update_datetime).days
                    stale_tables.append(table)
            else:
                logger.info(f"Table {table['name']} has no update_time")
        logger.info(f"Found {len(stale_tables)} additional stale tables.")

        return stale_tables

    @activity.defn
    async def tag_stale_tables(self, args: Dict[str, Any]) -> TagStaleTablesOutput:
        """Activity 3: Add an announcement to mark stale tables"""
        stale_tables = args["stale_tables"]
        output = TagStaleTablesOutput()
        client = await self._get_atlan_client()

        for table_info in stale_tables:
            try:
                logger.info(
                    f"Adding stale data announcement for {table_info['qualified_name']}"
                )

                announcement = Announcement(
                    announcement_type=AnnouncementType.WARNING,
                    announcement_title="Stale Data Detected",
                    announcement_message=f"This table contains stale data. Last updated: {table_info.get('stale_since', 'unknown')}. "
                    f"Data freshness check performed on {table_info.get('check_date', 'unknown')}.",
                )

                await client.asset.update_announcement(
                    asset_type=Table,
                    qualified_name=table_info["qualified_name"],
                    name=table_info["name"],
                    announcement=announcement,
                )

                output.tagged_count += 1
                logger.info(
                    f"✓ Stale data announcement added for {table_info['qualified_name']}"
                )

            except Exception as e:
                logger.info(
                    f"Failed to add announcement to table {table_info['qualified_name']}: {str(e)}"
                )
                output.failed_count += 1

        return output
