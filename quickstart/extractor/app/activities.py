from typing import Any, Dict
import os
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

from application_sdk.activities.common.utils import (
    get_workflow_id,
    get_workflow_run_id,
)
from .handler import ExtractorHandler
from application_sdk.inputs.statestore import StateStoreInput, StateType
from application_sdk.constants import TEMPORARY_PATH

logger = get_logger(__name__)
activity.logger = logger


class ExtractorActivities(ActivitiesInterface):
    """
    Activities for the Extractor app using the handler/client pattern.
    
    This class delegates to ExtractorHandler for all extraction operations,
    following the proper separation of concerns.
    """

    def __init__(self, extractor_handler: ExtractorHandler | None = None):
        """Initialize ExtractorActivities with a ExtractorHandler.

        Args:
            extractor_handler (Optional[ExtractorHandler]): Optional ExtractorHandler instance
        """
        self.extractor_handler = extractor_handler or ExtractorHandler()

    @activity.defn
    async def get_workflow_args(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get and merge workflow arguments with defaults.
        
        This method merges the provided configuration with default values
        to ensure all required parameters are available for the workflow.

        Args:
            config (Dict[str, Any]): Input configuration that may include:
                - input_file (str): Path to the input JSON file
                - output_file (str): Path for the output file (optional)

        Returns:
            Dict[str, Any]: Complete workflow configuration with defaults applied
        """

        workflow_id = workflow_config.get("workflow_id", get_workflow_id())
        if not workflow_id:
            raise ValueError("workflow_id is required in workflow_config")

        try:
            # This already handles the Dapr call internally
            workflow_args = StateStoreInput.get_state(workflow_id, StateType.WORKFLOWS)
            workflow_args["workflow_id"] = workflow_id
            workflow_args["workflow_run_id"] = get_workflow_run_id()
            return workflow_args

        except Exception as e:
            logger.error(
                f"Failed to retrieve workflow configuration for {workflow_id}: {str(e)}",
                exc_info=e,
            )
            raise
        
    @activity.defn
    async def extract_table_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and transform Table metadata from a JSON file.

        This activity delegates to the ExtractorHandler for all extraction operations,
        following the proper handler/client pattern.

        Args:
            config (Dict[str, Any]): Input configuration that may include:
                - input_file (str): Path to the input JSON file
                - output_file (str): Path for the output file (optional)

        Returns:
            Dict[str, Any]: Summary of the extraction process
        """
        # Extract and validate input parameters
        input_file: str = config.get("input_file", "extractor-app-input-table.json")
        output_file: str = config.get("output_file", "")

        logger.info(f"Processing extraction request for input file '{input_file}'")
        logger.info(f"Output file: '{output_file}'")

        try:
            # Delegate to the handler for extraction
            result = await self.extractor_handler.extract_and_transform(input_file, output_file)
            
            logger.info(f"Successfully completed extraction: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract table metadata: {e}", exc_info=True)
            # Return a structured error response instead of raising
            return {
                "status": "failed",
                "error": str(e),
                "input_file": input_file,
                "output_file": output_file,
                "raw_records": 0,
                "transformed_records": 0
            }

    @activity.defn
    async def test_extractor_connectivity(self) -> bool:
        """
        Test connectivity and basic functionality of the extractor.

        Returns:
            bool: True if extractor is working properly, False otherwise
        """
        try:
            logger.info("Testing extractor connectivity")
            result = await self.extractor_handler.test_auth()
            
            if result:
                logger.info("Extractor connectivity test passed")
            else:
                logger.warning("Extractor connectivity test failed")
                
            return result
            
        except Exception as e:
            logger.error(f"Extractor connectivity test failed with exception: {e}", exc_info=True)
            return False

    @activity.defn
    async def perform_preflight_check(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform preflight checks for extraction operations.

        Args:
            config (Dict[str, Any]): Configuration containing parameters to test

        Returns:
            Dict[str, Any]: Preflight check results
        """
        try:
            logger.info("Performing extractor preflight check")
            
            # Delegate to handler for preflight check
            result = await self.extractor_handler.preflight_check(config)
            
            logger.info(f"Preflight check completed with status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Preflight check failed with exception: {e}", exc_info=True)
            return {
                "status": "failed",
                "message": f"Preflight check failed: {e}",
                "checks": {
                    "client_initialization": False,
                    "file_access": False,
                    "json_parsing": False
                }
            }
