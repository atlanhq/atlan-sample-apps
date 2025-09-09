import json
import os
from typing import Any, Dict, List

from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class ExtractorClient:
    """Client for handling JSON file operations and data transformation."""

    def __init__(self):
        """Initialize the ExtractorClient."""
        self.credentials: Dict[str, Any] = {}

    async def read_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read and parse a JSON file containing Table asset information.

        Args:
            file_path (str): Path to the JSON file to read

        Returns:
            List[Dict[str, Any]]: List of Table asset dictionaries

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        try:
            logger.info(f"Reading JSON file: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            logger.info(f"Successfully read {len(data)} records from {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    async def transform_table_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw Table asset data into a standardized format.

        Args:
            raw_data (List[Dict[str, Any]]): Raw Table asset data from JSON

        Returns:
            List[Dict[str, Any]]: Transformed Table asset data
        """
        try:
            logger.info(f"Transforming {len(raw_data)} table records")
            
            transformed_data = []
            
            for item in raw_data:
                # Validate that this is a Table asset
                if item.get("Type") != "Table":
                    logger.warning(f"Skipping non-Table asset: {item.get('Type', 'Unknown')}")
                    continue
                
                # Transform the data into a standardized format
                transformed_item = {
                    "typeName": "Table",
                    "name": item.get("Name", ""),
                    "displayName": item.get("Display_Name", item.get("Name", "")),
                    "description": item.get("Description", ""),
                    "userDescription": item.get("User_Description", ""),
                    "ownerUsers": item.get("Owner_Users", "").split("\n") if item.get("Owner_Users") else [],
                    "ownerGroups": item.get("Owner_Groups", "").split("\n") if item.get("Owner_Groups") else [],
                    "certificateStatus": item.get("Certificate_Status", ""),
                    "schemaName": item.get("Schema_Name", ""),
                    "databaseName": item.get("Database_Name", ""),
                    "sourceCreatedAt": self._get_current_timestamp()
                }
                
                transformed_data.append(transformed_item)
            
            logger.info(f"Successfully transformed {len(transformed_data)} table records")
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error transforming table data: {e}")
            raise

    async def write_transformed_data(self, data: List[Dict[str, Any]], output_path: str) -> str:
        """
        Write transformed data to a JSON file.

        Args:
            data (List[Dict[str, Any]]): Transformed data to write
            output_path (str): Path where to write the output file

        Returns:
            str: Path to the written file
        """
        try:
            # Validate output path
            if not output_path or not output_path.strip():
                raise ValueError("Output path cannot be empty")
            
            # Ensure output directory exists (only if output_path has a directory)
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully wrote {len(data)} records to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error writing transformed data to {output_path}: {e}")
            raise

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    async def get_extraction_summary(self, input_path: str, output_path: str, 
                                   raw_count: int, transformed_count: int) -> Dict[str, Any]:
        """
        Generate a summary of the extraction process.

        Args:
            input_path (str): Path to the input file
            output_path (str): Path to the output file
            raw_count (int): Number of raw records processed
            transformed_count (int): Number of records successfully transformed

        Returns:
            Dict[str, Any]: Summary of the extraction process
        """
        return {
            "status": "success",
            "input_file": input_path,
            "output_file": output_path,
            "raw_records": raw_count,
            "transformed_records": transformed_count,
            "skipped_records": raw_count - transformed_count,
            "timestamp": self._get_current_timestamp()
        }
