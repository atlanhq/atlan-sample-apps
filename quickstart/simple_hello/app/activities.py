"""Activities for the simple hello world workflow."""

from application_sdk.activities import ActivitiesInterface
from temporalio import activity


class SimpleHelloActivities(ActivitiesInterface):
    """Activities for simple hello world workflow."""

    @activity.defn
    async def output_hello_world(self) -> str:
        """Output Hello World message.

        Returns:
            str: The hello world message
        """
        message = "Hello World !!"
        print(message)
        return message

