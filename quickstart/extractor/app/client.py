import os
from typing import Any, Dict, Optional, TextIO


class ClientClass:
    """Client for handling JSON file operations and data transformation."""

    def __init__(self):
        self.credentials: Dict[str, Any] = {}
        self.file_handler: Optional[TextIO] = None

    def create_read_handler(self, file_path: str) -> TextIO:
        """Create and return a file handler for the specified file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.file_handler:
            self.close_file_handler()

        self.file_handler = open(file_path, "r", encoding="utf-8")
        return self.file_handler

    def close_file_handler(self) -> None:
        """Close the current file handler if it exists."""
        if self.file_handler:
            self.file_handler.close()
            self.file_handler = None
