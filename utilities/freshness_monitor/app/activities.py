import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.clients.async_atlan import get_client
from pyatlan.client.aio import AsyncAtlanClient
from pyatlan.model.assets import Table, Asset
from pyatlan.model.core import Announcement
from pyatlan.model.enums import AnnouncementType
from pyatlan.model.fluent_search import FluentSearch
from temporalio import activity

logger = get_logger(__name__)


class FreshnessMonitorActivities(ActivitiesInterface):
    def __init__(self):
        self.atlan_client = None

    async def _get_atlan_client(self) -> AsyncAtlanClient:
        """Return the initialized Atlan client"""
        if self.atlan_client is None:
            self.atlan_client = await get_client()
        return self.atlan_client

    @activity.defn
    async def fetch_tables_metadata(
        self, workflow_args: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Activity 1: Fetch table metadata from Atlan"""
        client = await self._get_atlan_client()

        # Build search request for tables
        logger.info("Fetching tables metadata...")
        search_results = await (
            FluentSearch()
            .select()
            .where(Asset.TYPE_NAME.eq("Table"))
            .include_on_results(Asset.QUALIFIED_NAME)
            .include_on_results(Asset.NAME)
            .include_on_results(Asset.UPDATE_TIME)
            .include_on_results(Asset.CREATE_TIME)
            .page_size(30)
            .execute_async(client=client)
        )

        tables_data = []
        max_tables = 30  # Limit the number of tables to process
        count = 0

        # Iterate directly over search results with limit
        async for asset in search_results:
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
                logger.info(
                    f"Processed table {count}: {table_info['name']} {table_info}"
                )

                # Break after processing the desired number of tables
                if count >= max_tables:
                    logger.info(
                        f"Reached maximum limit of {max_tables} tables. Stopping."
                    )
                    break

        logger.info("Total tables processed: {count}")
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
        logger.info(f"Found {len(stale_tables)} stale tables.")

        return stale_tables

    @activity.defn
    async def tag_stale_tables(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Activity 3: Add an announcement to mark stale tables"""
        stale_tables = args["stale_tables"]

        client = await self._get_atlan_client()

        tagged_count = 0
        failed_count = 0

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

                tagged_count += 1
                logger.info(
                    f"✓ Stale data announcement added for {table_info['qualified_name']}"
                )

            except Exception as e:
                logger.info(
                    f"Failed to add announcement to table {table_info['qualified_name']}: {str(e)}"
                )
                failed_count += 1

        return {
            "tagged_count": tagged_count,
            "failed_count": failed_count,
            "total_stale_tables": len(stale_tables),
            "approach_used": "announcement_only",
        }
