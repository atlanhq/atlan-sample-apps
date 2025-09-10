from typing import Any, Dict, List, Tuple
import os
import json
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

from .handler import HandlerClass
logger = get_logger(__name__)
activity.logger = logger


class ActivitiesClass(ActivitiesInterface):
    """
    Activities for the Extractor app using the handler/client pattern.
    
    This class delegates to HandlerClass for all extraction operations,
    following the proper separation of concerns.
    """
    def __init__(self, handler: HandlerClass | None = None):
        """
        Args:
            handler (Optional[HandlerClass]): Optional HandlerClass instance
        """
        self.handler = handler or HandlerClass()

    def _validate_and_setup_config(self, config: Dict[str, Any]) -> Tuple[str, str]:
        """
        Validate configuration and setup file paths.
        
        Args:
            config (Dict[str, Any]): Input configuration
            
        Returns:
            Tuple[str, str]: (input_file_path, output_file_path)
            
        Raises:
            ValueError: If handler/client not initialized
            FileNotFoundError: If input file doesn't exist
        """
        if not self.handler or not self.handler.client:
            raise ValueError("Handler or extractor client not initialized")
        
        # Extract and validate input file
        input_file: str = config.get("input_file", "extractor-app-input-table.json")
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"File not found: {input_file}")
        logger.info(f"Processing extraction request for input file '{input_file}'")
        
        # Generate output file path if not provided
        output_file: str = config.get("output_file", "")
        if not output_file or not output_file.strip():
            base_name = os.path.splitext(input_file)[0] or "transformed_output"
            output_file = f"{base_name}_transformed.json"
            logger.info(f"Generated output file path: {output_file}")
        else:
            logger.info(f"Using provided output file path: {output_file}")
            
        return input_file, output_file

    def _read_input_data(self, input_file: str) -> List[Dict[str, Any]]:
        """
        Read and parse JSON data from input file.
        
        Args:
            input_file (str): Path to the input JSON file
            
        Returns:
            List[Dict[str, Any]]: Raw data from the input file
            
        Raises:
            json.JSONDecodeError: If file contains invalid JSON
        """
        client = self.handler.client
        file_handler = client.create_read_handler(input_file)
        raw_data = json.load(file_handler)
        
        raw_data_count = len(raw_data)
        logger.info(f"Read {raw_data_count} records using file handler")
        
        return raw_data

    def _transform_single_table_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single table item into standardized format.
        
        Args:
            item (Dict[str, Any]): Raw table item data
            
        Returns:
            Dict[str, Any]: Transformed table item
        """
        return {
            "typeName": "Table",
            "name": item.get("Name", ""),
            "displayName": item.get("Display_Name", item.get("Name", "")),
            "description": item.get("Description", ""),
            "userDescription": item.get("User_Description", ""),
            "ownerUsers": item.get("Owner_Users", "").split("\n") if item.get("Owner_Users") else [],
            "ownerGroups": item.get("Owner_Groups", "").split("\n") if item.get("Owner_Groups") else [],
            "certificateStatus": item.get("Certificate_Status", ""),
            "schemaName": item.get("Schema_Name", ""),
            "databaseName": item.get("Database_Name", "")
        }

    def _transform_table_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw data into standardized table format.
        
        Args:
            raw_data (List[Dict[str, Any]]): Raw data from input file
            
        Returns:
            List[Dict[str, Any]]: Transformed table data
        """
        transformed_data = []
        
        for item in raw_data:
            # Validate that this is a Table asset
            if item.get("Type") != "Table":
                logger.warning(f"Skipping non-Table asset: {item.get('Type', 'Unknown')}")
                continue
            
            transformed_item = self._transform_single_table_item(item)
            transformed_data.append(transformed_item)
        
        logger.info(f"Transformed {len(transformed_data)} table records")
        return transformed_data

    def _write_output_data(self, transformed_data: List[Dict[str, Any]], output_file: str) -> None:
        """
        Write transformed data to output file as newline-delimited JSON.
        
        Args:
            transformed_data (List[Dict[str, Any]]): Transformed data to write
            output_file (str): Path to output file
        """
        with open(output_file, 'w', encoding='utf-8') as file:
            for item in transformed_data:
                json.dump(item, file, ensure_ascii=False)
                file.write('\n')
        
        logger.info(f"Successfully wrote {len(transformed_data)} records to {output_file}")

    def _create_response_summary(self, status: str, input_file: str, output_file: str, 
                                raw_count: int, transformed_count: int, error: str = None) -> Dict[str, Any]:
        """
        Create standardized response summary.
        
        Args:
            status (str): Operation status ('success' or 'failed')
            input_file (str): Input file path
            output_file (str): Output file path
            raw_count (int): Number of raw records processed
            transformed_count (int): Number of successfully transformed records
            error (str, optional): Error message if operation failed
            
        Returns:
            Dict[str, Any]: Response summary dictionary
        """
        response = {
            "status": status,
            "input_file": input_file,
            "output_file": output_file,
            "raw_records": raw_count,
            "transformed_records": transformed_count
        }
        
        if status == "success":
            response["skipped_records"] = raw_count - transformed_count
        else:
            response["error"] = error or "Unknown error occurred"
            
        return response

    @activity.defn
    async def extract_and_transform_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and transform Table metadata from a JSON file.

        This activity delegates to the HandlerClass for all extraction operations,
        following the proper handler/client pattern. The method is modular with
        separate concerns for validation, reading, transformation, and writing.

        Args:
            config (Dict[str, Any]): Input configuration that may include:
                - input_file (str): Path to the input JSON file
                - output_file (str): Path for the output file (optional)

        Returns:
            Dict[str, Any]: Summary of the extraction process
        """
        input_file = ""
        output_file = ""
        raw_data_count = 0
        transformed_data_count = 0

        try:
            # Step 1: Validate configuration and setup file paths
            input_file, output_file = self._validate_and_setup_config(config)
            
            # Step 2: Read input data
            raw_data = self._read_input_data(input_file)
            raw_data_count = len(raw_data)
            
            # Step 3: Transform the data
            transformed_data = self._transform_table_data(raw_data)
            transformed_data_count = len(transformed_data)
            
            # Step 4: Write transformed data to output file
            self._write_output_data(transformed_data, output_file)
            
            # Step 5: Create and return success response
            return self._create_response_summary(
                "success", input_file, output_file, raw_data_count, transformed_data_count
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {input_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract and transform table metadata: {e}", exc_info=True)
            # Return a structured error response instead of raising
            return self._create_response_summary(
                "failed", input_file, output_file, raw_data_count, transformed_data_count, str(e)
            )
        finally:
            # Always close the file handler
            if self.handler and self.handler.client:
                self.handler.client.close_file_handler()
                logger.info("File handler closed successfully")