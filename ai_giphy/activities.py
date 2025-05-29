from typing import Any, Dict

# Assuming ai_agent.py is in the same directory
from ai_agent import get_chain
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class AIGiphyActivities(ActivitiesInterface):
    @activity.defn
    async def run_ai_agent(self, input_string: str) -> Dict[str, Any]:
        """
        Runs the AI agent with the given input string.

        Args:
            input_string (str): The input to send to the AI agent.

        Returns:
            Dict[str, Any]: The output from the AI agent.
        """
        try:
            logger.info(f"Received input for AI agent: {input_string}")
            chain = get_chain()
            result = chain.invoke({"input": input_string})
            logger.info(f"AI agent execution successful. Output: {result}")
            return result
        except Exception as e:
            logger.error(f"Error running AI agent: {e}")
            raise e
