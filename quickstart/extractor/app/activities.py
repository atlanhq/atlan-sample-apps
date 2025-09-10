import json
import os
from typing import Any, Dict

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

from .handler import HandlerClass

logger = get_logger(__name__)
activity.logger = logger


class ActivitiesClass(ActivitiesInterface):
    """Activities for the Extractor app using the handler/client pattern."""

    def __init__(self, handler: HandlerClass | None = None):
        self.handler = handler or HandlerClass()

    @activity.defn
    async def extract_and_transform_metadata(
        self, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract and transform Table metadata from JSON file."""
        input_file = output_file = ""

        try:
            if not self.handler or not self.handler.client:
                raise ValueError("Handler or extractor client not initialized")

            output_file = config.get("output_file", "")
            input_file = config.get("input_file")
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"File not found: {input_file}")

            raw_data = json.load(self.handler.client.create_read_handler(input_file))
            transformed_data = []
            for item in raw_data:
                if item.get("Type") == "Table":
                    transformed_data.append(
                        {
                            "typeName": "Table",
                            "name": item.get("Name", ""),
                            "description": item.get("Description", ""),
                            "schemaName": item.get("Schema_Name", ""),
                            "databaseName": item.get("Database_Name", ""),
                        }
                    )

            with open(output_file, "w", encoding="utf-8") as file:
                for item in transformed_data:
                    json.dump(item, file, ensure_ascii=False)
                    file.write("\n")

        except Exception as e:
            logger.error(
                f"Failed to extract and transform table metadata: {e}", exc_info=True
            )
            raise
        finally:
            if self.handler and self.handler.client:
                self.handler.client.close_file_handler()
