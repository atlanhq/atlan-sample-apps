import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from pyatlan.client.atlan import AtlanClient
from pyatlan.model.assets import Table
from pyatlan.model.enums import AnnouncementType
from pyatlan.model.search import IndexSearchRequest
from temporalio import activity
from pyatlan.client.constants import EVENT_STREAM, GET_TOKEN, PARSE_QUERY, UPLOAD_IMAGE
from pyatlan.model.response import AccessTokenResponse, AssetMutationResponse

logger = get_logger(__name__)


class FreshnessMonitorActivities(ActivitiesInterface):
    """
    Activity class for monitoring data freshness in Atlan assets.
    
    This class provides activities for:
    1. Fetching table metadata from Atlan
    2. Identifying stale tables based on configurable thresholds
    3. Tagging stale tables with announcements
    """
    
    # Configuration constants
    DEFAULT_MAX_TABLES = 30
    DEFAULT_THRESHOLD_DAYS = 1
    DEFAULT_CONNECTION_QUALIFIED_NAME = "default/snowflake/1703211402"
    
    # Required environment variables
    REQUIRED_ENV_VARS = ["ATLAN_BASE_URL", "API_TOKEN_GUID"]
    
    def __init__(self):
        """
        Initialize the FreshnessMonitorActivities class.
        
        Raises:
            ValueError: If required environment variables are missing.
        """
        # Load and validate configuration
        self.config = self._load_configuration()
        self._validate_configuration()
        
        # Initialize client as None - will be created lazily
        self._atlan_client: Optional[AtlanClient] = None
        
        logger.info("FreshnessMonitorActivities initialized successfully")

    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Returns:
            Dict[str, Any]: Configuration dictionary.
        """
        return {
            "base_url": os.getenv("ATLAN_BASE_URL"),
            "api_token_id": os.getenv("API_TOKEN_GUID"),
            "max_tables": int(os.getenv("MAX_TABLES", self.DEFAULT_MAX_TABLES)),
            "threshold_days": int(os.getenv("THRESHOLD_DAYS", self.DEFAULT_THRESHOLD_DAYS)),
            "connection_qualified_name": os.getenv(
                "CONNECTION_QUALIFIED_NAME", 
                self.DEFAULT_CONNECTION_QUALIFIED_NAME
            ),
        }

    def _validate_configuration(self) -> None:
        """
        Validate that all required configuration is present.
        
        Raises:
            ValueError: If required configuration is missing.
        """
        missing_vars = []
        
        for var in self.REQUIRED_ENV_VARS:
            env_key = var
            config_key = var.lower().replace("_", "_")
            
            if var == "ATLAN_BASE_URL":
                config_key = "base_url"
            elif var == "API_TOKEN_GUID":
                config_key = "api_token_id"
                
            if not self.config.get(config_key):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        
        logger.info("Configuration validation successful")

    async def _get_atlan_client(self) -> AtlanClient:
        """
        Get or create the Atlan client instance.
        
        Returns:
            AtlanClient: The initialized Atlan client.
            
        Raises:
            Exception: If client initialization fails.
        """
        if self._atlan_client is None:
            try:
                logger.info("Initializing Atlan client...")
                self._atlan_client = AtlanClient.from_token_guid(guid=self.config["api_token_id"])
                logger.info("Atlan client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Atlan client: {str(e)}")
                raise
        
        return self._atlan_client

    def _build_table_search_request(self, max_tables: int = None) -> IndexSearchRequest:
        """
        Build search request for fetching table metadata.
        
        Args:
            max_tables: Maximum number of tables to fetch (defaults to DEFAULT_MAX_TABLES).
            
        Returns:
            IndexSearchRequest: Configured search request for tables.
        """
        if max_tables is None:
            max_tables = self.config["max_tables"]
            
        return IndexSearchRequest(
            dsl={
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"__typeName.keyword": "Table"}},
                            {"term": {"__state": "ACTIVE"}},
                            {
                                "term": {
                                    "connectionQualifiedName": self.config["connection_qualified_name"]
                                }
                            },
                        ]
                    }
                },
                "from": 0,
                "size": max_tables,
                "attributes": [
                    "qualifiedName",
                    "name",
                    "lastUpdatedAt",
                ],
            }
        )

    @activity.defn
    async def fetch_tables_metadata(
        self, workflow_args: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Activity 1: Fetch table metadata from Atlan.
        
        This activity searches for active tables in the specified connection
        and returns their metadata including name, qualified name, and timestamps.
        
        Args:
            workflow_args: Dictionary containing workflow arguments (currently unused).
            
        Returns:
            List[Dict[str, Any]]: List of table metadata dictionaries containing:
                - qualified_name: Unique identifier for the table
                - name: Display name of the table
                - update_time: Last update timestamp (in milliseconds)
                - create_time: Creation timestamp (in milliseconds)
                - guid: Unique GUID for the table
                
        Raises:
            Exception: If client initialization or search fails.
        """
        try:
            client = await self._get_atlan_client()
            logger.info("Fetching tables metadata...")
            
            # Build search request for tables
            search_request = self._build_table_search_request()
            logger.info(f"Built search request: {search_request}")
            
            tables_data = []
            count = 0
            
            # Iterate directly over search results with limit
            for asset in client.asset.search(search_request):
                if isinstance(asset, Table):
                    table_info = self._extract_table_info(asset)
                    tables_data.append(table_info)
                    count += 1
                    
                    logger.info(f"Processed table {count}: {table_info['name']}")
                    
                    # Break after processing the desired number of tables
                    if count >= self.config["max_tables"]:
                        logger.info(f"Reached maximum limit of {self.config['max_tables']} tables. Stopping.")
                        break
            
            logger.info(f"Successfully fetched metadata for {count} tables")
            return tables_data
            
        except Exception as e:
            logger.error(f"Failed to fetch tables metadata: {str(e)}")
            raise

    def _extract_table_info(self, asset: Table) -> Dict[str, Any]:
        """
        Extract relevant information from a Table asset.
        
        Args:
            asset: Table asset from Atlan.
            
        Returns:
            Dict[str, Any]: Dictionary containing table information.
        """
        return {
            "qualified_name": asset.attributes.qualified_name,
            "name": asset.attributes.name,
            "update_time": asset.update_time,  # Already a timestamp number
            "create_time": asset.create_time,  # Already a timestamp number
            "guid": asset.guid,
        }

    @activity.defn
    async def identify_stale_tables(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Activity 2: Filter and identify stale tables based on configurable threshold.
        
        This activity processes table metadata to identify tables that haven't been
        updated within the specified threshold period.
        
        Args:
            args: Dictionary containing:
                - tables_data: List of table metadata from fetch_tables_metadata
                - threshold_days (optional): Number of days to consider as stale threshold
                
        Returns:
            List[Dict[str, Any]]: List of stale table dictionaries with additional fields:
                - stale_since: ISO timestamp when table became stale
                - days_stale: Number of days the table has been stale
                
        Raises:
            KeyError: If required arguments are missing.
            Exception: If processing fails.
        """
        try:
            # Extract arguments with validation
            if "tables_data" not in args:
                raise KeyError("Missing required argument: tables_data")
                
            tables_data = args["tables_data"]
            threshold_days = args.get("threshold_days", self.config["threshold_days"])
            
            logger.info(f"Identifying stale tables with {threshold_days}-day threshold...")
            
            stale_tables = []
            threshold_date = datetime.now() - timedelta(days=threshold_days)
            
            for table in tables_data:
                try:
                    stale_info = self._check_table_staleness(table, threshold_date)
                    if stale_info:
                        stale_tables.append(stale_info)
                except Exception as e:
                    logger.warning(f"Failed to process table {table.get('name', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Identified {len(stale_tables)} stale tables out of {len(tables_data)} total tables")
            return stale_tables
            
        except Exception as e:
            logger.error(f"Failed to identify stale tables: {str(e)}")
            raise

    def _check_table_staleness(self, table: Dict[str, Any], threshold_date: datetime) -> Optional[Dict[str, Any]]:
        """
        Check if a table is stale based on its update time.
        
        Args:
            table: Table metadata dictionary.
            threshold_date: DateTime threshold for staleness.
            
        Returns:
            Optional[Dict[str, Any]]: Table dict with staleness info if stale, None otherwise.
        """
        update_time = table.get("update_time")
        if not update_time:
            logger.warning(f"Table {table.get('name', 'unknown')} has no update_time")
            return None
        
        # Convert timestamp to datetime if needed
        update_datetime = self._convert_timestamp_to_datetime(update_time)
        
        if update_datetime < threshold_date:
            # Create a copy of the table with staleness information
            stale_table = table.copy()
            stale_table["stale_since"] = threshold_date.isoformat()
            stale_table["days_stale"] = (datetime.now() - update_datetime).days
            stale_table["check_date"] = datetime.now().isoformat()
            return stale_table
        
        return None

    def _convert_timestamp_to_datetime(self, timestamp: Any) -> datetime:
        """
        Convert various timestamp formats to datetime object.
        
        Args:
            timestamp: Timestamp in various formats (int, float, datetime).
            
        Returns:
            datetime: Converted datetime object.
            
        Raises:
            ValueError: If timestamp format is not supported.
        """
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            # Assuming milliseconds, convert to seconds
            return datetime.fromtimestamp(timestamp / 1000)
        else:
            raise ValueError(f"Unsupported timestamp format: {type(timestamp)}")

    @activity.defn
    async def tag_stale_tables(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Activity 3: Add announcements to mark stale tables.
        
        This activity creates warning announcements on stale tables to notify users
        about data freshness issues.
        
        Args:
            args: Dictionary containing:
                - stale_tables: List of stale table metadata from identify_stale_tables
                
        Returns:
            Dict[str, Any]: Summary of tagging operation containing:
                - tagged_count: Number of successfully tagged tables
                - failed_count: Number of tables that failed to be tagged
                - total_stale_tables: Total number of stale tables processed
                - approach_used: Method used for tagging (announcement_only)
                - errors: List of error details for failed operations
                
        Raises:
            KeyError: If required arguments are missing.
            Exception: If client initialization fails.
        """
        try:
            # Validate arguments
            if "stale_tables" not in args:
                raise KeyError("Missing required argument: stale_tables")
                
            stale_tables = args["stale_tables"]
            logger.info(f"Starting to tag {len(stale_tables)} stale tables...")
            
            client = await self._get_atlan_client()
            
            tagged_count = 0
            failed_count = 0
            errors = []
            
            for table in stale_tables:
                try:
                    self._tag_single_table(client, table)
                    tagged_count += 1
                    logger.info(f"✓ Successfully tagged table: {table.get('qualified_name', 'unknown')}")
                    
                except Exception as e:
                    error_msg = f"Failed to tag table {table.get('qualified_name', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append({
                        "table": table.get('qualified_name', 'unknown'),
                        "error": str(e)
                    })
                    failed_count += 1
            
            result = {
                "tagged_count": tagged_count,
                "failed_count": failed_count,
                "total_stale_tables": len(stale_tables),
                "approach_used": "announcement_only",
                "errors": errors
            }
            
            logger.info(f"Tagging completed: {tagged_count} successful, {failed_count} failed")
            return result
            
        except Exception as e:
            logger.error(f"Failed to tag stale tables: {str(e)}")
            raise

    def _tag_single_table(self, client: AtlanClient, table: Dict[str, Any]) -> None:
        """
        Tag a single table with stale data announcement.
        
        Args:
            client: Initialized Atlan client.
            table: Table metadata dictionary.
            
        Raises:
            Exception: If tagging operation fails.
        """
        qualified_name = table.get("qualified_name")
        name = table.get("name")
        
        if not qualified_name or not name:
            raise ValueError("Table missing required fields: qualified_name or name")
        
        logger.info(f"Adding stale data announcement for {qualified_name}")
        
        # Create minimal table object for update
        table_with_announcement = Table.updater(
            qualified_name=qualified_name, 
            name=name
        )
        
        # Configure announcement
        announcement_config = self._create_announcement_config(table)
        table_with_announcement.announcement_type = announcement_config["type"]
        table_with_announcement.announcement_title = announcement_config["title"]
        table_with_announcement.announcement_message = announcement_config["message"]
        
        # Save the announcement
        client.asset.save(table_with_announcement)

    def _create_announcement_config(self, table: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create announcement configuration for a stale table.
        
        Args:
            table: Table metadata dictionary with staleness information.
            
        Returns:
            Dict[str, Any]: Announcement configuration with type, title, and message.
        """
        stale_since = table.get('stale_since', 'unknown')
        check_date = table.get('check_date', 'unknown')
        days_stale = table.get('days_stale', 'unknown')
        
        return {
            "type": AnnouncementType.WARNING,
            "title": "Stale Data Detected",
            "message": (
                f"This table contains stale data. "
                f"Last updated: {stale_since}. "
                f"Days stale: {days_stale}. "
                f"Data freshness check performed on {check_date}."
            )
        }
