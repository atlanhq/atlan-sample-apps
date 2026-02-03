from typing import Any, Dict

from app.handler import HandlerClass
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class ActivitiesClass(ActivitiesInterface):
    def __init__(self, handler: HandlerClass | None = None):
        self.handler = handler or HandlerClass()

    @activity.defn
    async def get_workflow_args(
        self, workflow_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """TODO: Process and merge workflow configuration."""
        return workflow_config

    @activity.defn
    async def extract_and_transform_metadata(
        self, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """TODO: Implement your extraction and transformation logic."""
        raise NotImplementedError("Implement this activity")
