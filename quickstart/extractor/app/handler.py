import os
from typing import Any, Dict

from application_sdk.handlers import HandlerInterface
from application_sdk.observability.logger_adaptor import get_logger

from .client import ExtractorClient

logger = get_logger(__name__)


class ExtractorHandler(HandlerInterface):
    """Extractor app handler for Atlan SDK interactions.
    
    This handler provides the SDK interface for data extraction operations,
    coordinating between the frontend, SDK, and the ExtractorClient.
    
    CALL CHAIN: Frontend --> SDK --> ExtractorHandler --> ExtractorClient --> File System
    """

    def __init__(self, client: ExtractorClient | None = None):
        """Initialize Extractor handler with optional client instance.

        Args:
            client (Optional[ExtractorClient]): Optional ExtractorClient instance
        """
        self.extractor_client = client or ExtractorClient()

    # ============================================================================
    # SECTION 1: SDK INTERFACE METHODS (Called by FastAPI endpoints)
    # ============================================================================

    async def load(self, credentials: Dict[str, Any]) -> None:
        """SDK interface: Initialize Extractor client with credentials.
        
        For file-based extraction, credentials may contain file paths or
        configuration options.

        Args:
            credentials (Dict[str, Any]): Configuration dict
        """
        if self.extractor_client:
            self.extractor_client.credentials = credentials
            logger.debug("Loaded credentials for Extractor client")

    async def test_auth(self) -> bool:
        """SDK interface: Test file system access and JSON parsing.
        
        Tests basic file operations and JSON parsing capabilities.

        Returns:
            bool: True if file operations are accessible, False otherwise
        """
        try:
            if not self.extractor_client:
                raise Exception("Extractor client not initialized")

            # Test with a simple JSON structure
            test_data = [{"Type": "Table", "Name": "test", "Description": "test"}]
            transformed = await self.extractor_client.transform_table_data(test_data)
            
            if len(transformed) == 1 and transformed[0]["asset_type"] == "Table":
                logger.info("Extractor client test successful")
                return True
            else:
                logger.warning("Extractor client test failed - transformation issue")
                return False
            
        except Exception as e:
            logger.error(f"Extractor client test failed: {e}")
            return False

    async def fetch_metadata(self, metadata_type: str = "table", database: str = "") -> Dict[str, Any]:
        """SDK interface: Fetch metadata from JSON files.
        
        This method reads and transforms Table asset metadata from JSON files.

        Args:
            metadata_type (str): Type of metadata to fetch (default: "table")
            database (str): Database name (ignored for file-based extraction)

        Returns:
            Dict[str, Any]: Transformed metadata
        """
        try:
            logger.info(f"Fetching metadata for type: {metadata_type}")
            
            # For now, we'll use a default input file path
            # In a real implementation, this could be configurable
            input_file = "extractor-app-input-table.json"
            
            if not self.extractor_client:
                raise Exception("Extractor client not initialized")
            
            # Read the JSON file
            raw_data = await self.extractor_client.read_json_file(input_file)
            
            # Transform the data
            transformed_data = await self.extractor_client.transform_table_data(raw_data)
            
            return {
                "success": True,
                "data": transformed_data,
                "count": len(transformed_data),
                "source": input_file
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch metadata: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0
            }

    async def preflight_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """SDK interface: Perform preflight checks for extraction operations.

        Args:
            payload (Dict[str, Any]): Request payload containing operation parameters

        Returns:
            Dict[str, Any]: Preflight check results
        """
        try:
            logger.info("Performing extractor preflight check")
            
            # Test client initialization
            client_ok = await self.test_auth()
            if not client_ok:
                return {
                    "status": "failed",
                    "message": "Failed to initialize extractor client",
                    "checks": {
                        "client_initialization": False,
                        "file_access": False,
                        "json_parsing": False
                    }
                }

            # Test file access (check if default input file exists)
            input_file = payload.get("input_file", "extractor-app-input-table.json")
            file_exists = False
            try:
                import os
                file_exists = os.path.exists(input_file)
            except Exception as e:
                logger.warning(f"Could not check file existence: {e}")

            # Test JSON parsing if file exists
            json_parsing_ok = False
            if file_exists:
                try:
                    raw_data = await self.extractor_client.read_json_file(input_file)
                    json_parsing_ok = len(raw_data) > 0
                except Exception as e:
                    logger.warning(f"JSON parsing test failed: {e}")

            overall_status = "passed" if all([client_ok, file_exists, json_parsing_ok]) else "failed"
            
            return {
                "status": overall_status,
                "message": f"Preflight check {overall_status}",
                "checks": {
                    "client_initialization": client_ok,
                    "file_access": file_exists,
                    "json_parsing": json_parsing_ok
                },
                "details": {
                    "input_file": input_file,
                    "file_exists": file_exists,
                    "tested_at": self.extractor_client._get_current_timestamp()
                }
            }
            
        except Exception as e:
            logger.error(f"Preflight check failed with unexpected error: {e}", exc_info=True)
            return {
                "status": "failed",
                "message": f"Preflight check failed: {e}",
                "checks": {
                    "client_initialization": False,
                    "file_access": False,
                    "json_parsing": False
                }
            }

    # ============================================================================
    # SECTION 2: EXTRACTOR-SPECIFIC METHODS
    # ============================================================================

    async def extract_and_transform(self, input_file: str, output_file: str = None) -> Dict[str, Any]:
        """Extract and transform Table asset data from a JSON file.

        Args:
            input_file (str): Path to the input JSON file
            output_file (str): Path for the output file (optional)

        Returns:
            Dict[str, Any]: Summary of the extraction process
        """
        try:
            logger.info(f"Starting extraction from {input_file}")
            logger.info(f"Output file specified: {output_file}")
            
            if not self.extractor_client:
                raise Exception("Extractor client not initialized")

            # Generate output file path if not provided
            if not output_file or output_file.strip() == "":
                base_name = os.path.splitext(input_file)[0]
                if not base_name:
                    base_name = "transformed_output"
                output_file = f"{base_name}_transformed.json"
                logger.info(f"Generated output file path: {output_file}")
            else:
                logger.info(f"Using provided output file path: {output_file}")

            # Read the JSON file
            raw_data = await self.extractor_client.read_json_file(input_file)
            raw_count = len(raw_data)

            # Transform the data
            transformed_data = await self.extractor_client.transform_table_data(raw_data)
            transformed_count = len(transformed_data)

            # Write the transformed data
            await self.extractor_client.write_transformed_data(transformed_data, output_file)

            # Generate summary
            summary = await self.extractor_client.get_extraction_summary(
                input_file, output_file, raw_count, transformed_count
            )
            
            logger.info(f"Extraction completed successfully: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to extract and transform data: {e}", exc_info=True)
            raise
