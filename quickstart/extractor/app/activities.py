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
