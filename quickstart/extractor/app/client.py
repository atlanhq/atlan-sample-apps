import os
from typing import Any, Dict, Optional, TextIO

from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


class ClientClass:
    """Client for handling JSON file operations and data transformation."""

    def __init__(self):
        """Initialize the ExtractorClient."""
        self.credentials: Dict[str, Any] = {}
        self.file_handler: Optional[TextIO] = None

    def create_read_handler(self, file_path: str) -> TextIO:
        """
        Create and return a file handler for the specified JSON file.

        Args:
            file_path (str): Path to the JSON file to open

        Returns:
            TextIO: File handler for the opened file

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error opening the file
        """
        try:
            logger.info(f"Creating file handler for: {file_path}")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Close existing handler if any
            if self.file_handler:
                self.close_file_handler()

            # Open new file handler
            self.file_handler = open(file_path, "r", encoding="utf-8")

            logger.info(f"Successfully created file handler for: {file_path}")
            return self.file_handler

        except Exception as e:
            logger.error(f"Error creating file handler for {file_path}: {e}")
            raise

    def close_file_handler(self) -> None:
        """
        Close the current file handler if it exists.

        This method ensures proper cleanup of file resources and should be called
        when the file operations are complete.
        """
        try:
            if self.file_handler:
                logger.info("Closing file handler")
                self.file_handler.close()
                self.file_handler = None
                logger.info("File handler closed successfully")
            else:
                logger.debug("No file handler to close")

        except Exception as e:
            logger.error(f"Error closing file handler: {e}")
            # Reset handler state even if close fails
            self.file_handler = None
            raise
