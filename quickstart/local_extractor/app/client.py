import os
from typing import Optional, TextIO

from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class ClientClass:
    """Client for handling JSON file operations and resource management."""

    def __init__(self):
        # Template: Initialize file handler attribute
        self.file_handler: Optional[TextIO] = None

    # ========== ✨ CUSTOM METHODS ADDED ==========
    def create_read_handler(self, file_path: str) -> TextIO:
        """Create and return a file handler for reading JSON files."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.file_handler:
            self.close_file_handler()

        self.file_handler = open(file_path, "r", encoding="utf-8")
        logger.info(f"Created file handler for: {file_path}")
        return self.file_handler

    def close_file_handler(self) -> None:
        """Close the current file handler and clean up resources."""
        if self.file_handler:
            self.file_handler.close()
            self.file_handler = None
            logger.info("File handler closed successfully")

    # ========== ✨ END CUSTOM METHODS ==========
