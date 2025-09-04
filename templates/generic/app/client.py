from typing import Any, Dict, Optional

from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class ClientClass:
    """
    Client for connecting to the external system.
    """

    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        """Initialize client.

        Args:
            credentials (Optional[Dict[str, Any]]): Optional credentials dict.
        """
        self.credentials = credentials or {}
