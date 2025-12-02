from typing import Any, Dict

# Assuming ai_agent.py is in the same directory
from app.ai_agent import get_chain
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class AIGiphyActivities(ActivitiesInterface):
    @activity.defn
    async def run_ai_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the AI agent with the given input string and configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - ai_input_string (str): The input to send to the AI agent
                - openai_api_key (str, optional): OpenAI API key (falls back to env var)
                - openai_model_name (str, optional): OpenAI model name (falls back to env var, then default)
                - openai_base_url (str, optional): OpenAI base URL (falls back to env var)
                - giphy_api_key (str, optional): Giphy API key (falls back to env var)
                - smtp_host (str, optional): SMTP host (falls back to env var, then default)
                - smtp_port (int, optional): SMTP port (falls back to env var, then default)
                - smtp_username (str, optional): SMTP username (falls back to env var, then default)
                - smtp_password (str, optional): SMTP password (falls back to env var)
                - smtp_sender (str, optional): SMTP sender email (falls back to env var)

        Returns:
            Dict[str, Any]: The output from the AI agent.
        """
        try:
            input_string = config.get(
                "ai_input_string", "Fetch a cat gif and send it to test@example.com"
            )
            logger.info(f"Received input for AI agent: {input_string}")

            # Extract config for get_chain (exclude ai_input_string)
            chain_config = {k: v for k, v in config.items() if k != "ai_input_string"}
            chain = get_chain(chain_config)
            result = chain.invoke({"input": input_string})
            logger.info(f"AI agent execution successful. Output: {result}")
            return result
        except Exception as e:
            logger.error(f"Error running AI agent: {e}")
            raise e
