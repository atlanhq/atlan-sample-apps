from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class HelloWorldActivities(ActivitiesInterface):
    @activity.defn
    async def say_hello(self, name: str) -> str:
        """
        Say hello to the given name asynchronously.

        Args:
            name (str): The name to greet

        Returns:
            str: A greeting message
        """
        logger.info(f"Saying hello to {name}")
        return f"Hello, {name}!"
