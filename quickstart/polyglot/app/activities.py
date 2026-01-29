"""Activities for the polyglot sample app.

This module defines Temporal activities that demonstrate calling Java code
from Python using JPype for cross-language integration.
"""

from typing import Any, Dict

import pandas as pd
from app.utils.processor import FactorialProcessor
from application_sdk.activities import ActivitiesInterface
from application_sdk.io.json import JsonFileWriter
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class PolyglotActivities(ActivitiesInterface):
    """Activities for polyglot (Python-Java) demonstration.

    This class provides Temporal activities that showcase how to call
    Java methods from Python code using JPype integration.
    """

    @activity.defn
    async def calculate_factorial(self, number: int) -> Dict[str, Any]:
        """Calculate factorial using Java implementation.

        This activity demonstrates polyglot programming by calling a Java
        method from Python to calculate the factorial of a number.

        Args:
            number: The number to calculate factorial for (0-20).

        Returns:
            Dict[str, Any]: A dictionary containing:
                - result: The factorial result
                - input: The input number
                - success: Whether calculation succeeded
                - error: Error message if failed (optional)

        Example:
            >>> result = await calculate_factorial(5)
            >>> print(result)
            {'result': 120, 'input': 5, 'success': True}
        """
        logger.info(f"Activity: calculate_factorial called with number={number}")

        try:
            # Use the Java processor with context manager
            with FactorialProcessor(number=number) as processor:
                # Calculate factorial using Java
                result = processor.calculate()

                logger.info(f"Activity completed: {result}")
                return result

        except Exception as e:
            error_msg = f"Activity failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "result": None,
                "input": number,
                "success": False,
                "error": error_msg,
            }

    @activity.defn
    async def save_result_to_json(
        self, calculation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save factorial calculation result to a JSON file.

        This activity demonstrates using the SDK's JsonFileWriter to write
        results to a JSON file on disk.

        Args:
            calculation_result: The factorial calculation result containing:
                - result: The factorial value
                - input: The input number
                - success: Whether calculation succeeded

        Returns:
            Dict[str, Any]: Statistics about the saved file:
                - file_path: Path to the saved file
                - record_count: Number of records written
                - success: Whether save succeeded

        Example:
            >>> result = {"result": 120, "input": 5, "success": True}
            >>> stats = await save_result_to_json(result)
            >>> print(stats)
            {'file_path': '/tmp/output/results/factorial_result.json', ...}
        """
        logger.info(
            f"Activity: save_result_to_json called with result: {calculation_result}"
        )

        try:
            # Create a DataFrame from the result
            df = pd.DataFrame([calculation_result])
            output_path = calculation_result["output_path"]
            # Initialize JsonFileWriter
            json_output = JsonFileWriter(
                output_suffix="results",
                output_path=output_path,
                typename="factorial_result",
            )

            # Write the DataFrame to JSON
            await json_output.write_dataframe(df)

            # Get statistics
            stats = await json_output.get_statistics(typename="factorial_result")

            result = {
                "file_path": f"{output_path}/results/factorial_result",
                "record_count": stats.total_record_count,
                "chunk_count": stats.chunk_count,
                "success": True,
            }

            logger.info(f"Successfully saved result to JSON: {result}")
            return result

        except Exception as e:
            error_msg = f"Failed to save result to JSON: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "file_path": None,
                "record_count": 0,
                "chunk_count": 0,
                "success": False,
                "error": error_msg,
            }
