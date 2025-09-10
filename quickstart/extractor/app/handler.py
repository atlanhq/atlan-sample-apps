import os
from abc import ABC, abstractmethod
from typing import Any, Dict

from application_sdk.handlers import HandlerInterface
from application_sdk.observability.logger_adaptor import get_logger

from .client import ClientClass

logger = get_logger(__name__)


class HandlerClass(ABC):
    """Extractor app handler for Atlan SDK interactions.

    This handler provides the SDK interface for data extraction operations,
    coordinating between the frontend, SDK, and the ClientClass.

    CALL CHAIN: Frontend --> SDK --> HandlerClass --> ClientClass --> File System
    """

    def __init__(self, client: ClientClass | None = None):
        """Initialize Extractor handler with optional client instance.

        Args:
            client (Optional[ClientClass]): Optional ClientClass instance
        """
        self.client = client or ClientClass()
