import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from pyatlan.client.atlan import AtlanClient
from pyatlan.model.assets import Table
from pyatlan.model.core import Announcement
from pyatlan.model.enums import AnnouncementType
from pyatlan.model.search import IndexSearchRequest
from temporalio import activity

logger = get_logger(__name__)


class FreshnessMonitorActivities(ActivitiesInterface):
    def __init__(self):
        # Initialize AtlanClient immediately
        base_url = os.getenv("ATLAN_BASE_URL")
        api_key = os.getenv("ATLAN_API_KEY")

        if not base_url or not api_key:
            raise ValueError(
                "Missing required environment variables: ATLAN_BASE_URL and/or ATLAN_API_KEY"
            )

        # Create the client and set it as current immediately
        self.atlan_client = AtlanClient(base_url=base_url, api_key=api_key)

    async def _get_atlan_client(self) -> AtlanClient:
        """Return the initialized Atlan client"""
        return self.atlan_client

    @activity.defn
    async def fetch_tables_metadata(
        self, workflow_args: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Activity 1: Fetch table metadata from Atlan"""
        client = await self._get_atlan_client()

        # Build search request for tables
        logger.info("Fetching tables metadata...")
        search_request = IndexSearchRequest(
            dsl={
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"__typeName.keyword": "Table"}},
                            {"term": {"__state": "ACTIVE"}},
                        ]
                    }
                },
                "from": 0,
                "size": 30,
                "attributes": [
                    "qualifiedName",
                    "name",
                    "lastUpdatedAt",
                ],
            }
        )

        logger.info("search_request", search_request)
        logger.info("search_request", type(search_request))

        tables_data = []
        max_tables = 30  # Limit the number of tables to process
        count = 0

        # Iterate directly over search results with limit
        for asset in client.asset.search(search_request):
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

        logger.info(f"Total tables processed: {count}")
        return tables_data

    @activity.defn
    async def identify_stale_tables(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Activity 2: Filter and identify stale tables based on threshold"""
        tables_data = args["tables_data"]
        threshold_days = args["threshold_days"] or os.getenv("THRESHOLD_DAYS")

        stale_tables = []
        threshold_date = datetime.now() - timedelta(days=threshold_days)

        for table in tables_data:
            # Check if table is stale based on update_time
            update_time = table.get("update_time")
            if update_time:
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

        return stale_tables

    @activity.defn
    async def tag_stale_tables(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Activity 3: Add announcement to mark stale tables"""
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

                table = client.asset.update_announcement(
                    asset_type=Table,
                    qualified_name=table_info["qualified_name"],
                    name=table_info["name"],
                    announcement=announcement,
                )

                # Save the announcement
                client.asset.save(table)
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
