from typing import Any, Dict

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class HelloWorldActivities(ActivitiesInterface):
    @activity.defn
    async def say_hello(self, name: str) -> str:
        logger.info(f"Saying hello to {name}")
        return f"Hello, {name}!"

    @activity.defn
    def say_hello_sync(self, name: str) -> str:
        logger.info(f"Saying hello to {name}")
        return f"Hello, {name}!"

    @activity.defn
    async def get_workflow_args(
        self, workflow_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get workflow arguments from the config.
        For Kafka-triggered workflows, the args are passed directly in the config.
        """
        logger.info(f"Getting workflow args from config: {workflow_config}")
        # If workflow_args is in config, return it; otherwise return the config itself
        return workflow_config.get("workflow_args", workflow_config)
