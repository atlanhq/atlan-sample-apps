from typing import Any, Dict

from app.client.client import ClientClass
from application_sdk.handlers import HandlerInterface
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class HandlerClass(HandlerInterface):
    """App handler for Atlan SDK interactions.

    This handler provides the SDK interface for metadata operations,
    coordinating between the frontend, SDK, and the Client.


    SDK BEHAVIOR: Base handler automatically calls load() with credentials before calling any method,
    then wraps responses in standard format ({"success": true/false, "data": ...})
    """

    def __init__(self, client: ClientClass | None = None):
        """Initialize handler with optional client instance.

        Args:
            client (Optional[ApiClient]): Optional ApiClient instance
        """
        self.client = client or ClientClass()

    async def load(self, credentials: Dict[str, Any]) -> None:
        """SDK interface: Initialize client with credentials.

        Args:
            credentials (Dict[str, Any]): Configuration dict
        """
        if self.self.client:
            self.self.client.credentials = credentials
            logger.debug("Loaded credentials")

    async def test_auth(self) -> bool:
        try:
            # TODO: Implement connectivity test
            logger.info("connectivity test successful")
            return True

        except Exception as e:
            logger.error(f"connectivity test failed: {e}")
            return False

    async def fetch_metadata(self) -> Dict[str, Any]:
        """

        This method exists to satisfy the HandlerInterface

        Args:
            metadata_type (str): Type of metadata to fetch (ignored)
            database (str): Database name (ignored)

        Returns:
            Dict[str, Any]: Empty response indicating this operation is not supported
        """
        return {}

    async def preflight_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """SDK interface: Perform preflight checks for metadata operations.

        Args:
            payload (Dict[str, Any]): Request payload containing operation parameters

        Returns:
            Dict[str, Any]: Preflight check results
        """
        try:
            logger.info("Performing preflight check")
            return {"status": "passed", "message": "Preflight check passed"}

        except Exception as e:
            logger.error(
                f"Preflight check failed with unexpected error: {e}", exc_info=True
            )
            return {
                "status": "failed",
                "message": f"Preflight check failed: {e}",
                "checks": {},
            }
