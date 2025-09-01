from typing import Any, Dict

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

from .handler import WeatherHandler

logger = get_logger(__name__)
activity.logger = logger


class WeatherActivities(ActivitiesInterface):
    """
    Activities for the Weather app using the handler/client pattern.
    
    This class now delegates to WeatherHandler for all weather operations,
    following the proper separation of concerns.
    """

    def __init__(self, weather_handler: WeatherHandler | None = None):
        """Initialize WeatherActivities with a WeatherHandler.

        Args:
            weather_handler (Optional[WeatherHandler]): Optional WeatherHandler instance
        """
        self.weather_handler = weather_handler or WeatherHandler()

    @activity.defn
    async def get_weather_summary(self, config: Dict[str, Any]) -> str:
        """
        Build a friendly weather summary for the provided user and city.

        This activity now delegates to the WeatherHandler for all weather operations,
        following the proper handler/client pattern.

        Args:
            config (Dict[str, Any]): Input configuration that may include:
                - username (str): Name of the user to greet
                - city (str): City name to look up (default: "London")
                - units (str): "celsius" or "fahrenheit" (also accepts "metric"/"imperial")

        Returns:
            str: Summary string, e.g., "Hello Alice! Weather in London: 23°C, Clear sky"
        """
        # Extract and validate input parameters
        username: str = (config.get("username") or "Friend").strip() or "Friend"
        city: str = (config.get("city") or "London").strip() or "London"
        units: str = (config.get("units") or "celsius").strip() or "celsius"

        logger.info(f"Processing weather summary request for user '{username}', city '{city}', units '{units}'")

        try:
            # Delegate to the handler for weather summary generation
            summary = await self.weather_handler.get_weather_summary(username, city, units)
            
            logger.info(f"Successfully generated weather summary: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get weather summary: {e}", exc_info=True)
            # Return a friendly error message instead of raising
            return f"Hello {username}! Sorry, I couldn't get the weather for {city} right now. Please try again later."

    @activity.defn
    async def test_weather_connectivity(self) -> bool:
        """
        Test connectivity to the weather API.

        Returns:
            bool: True if API is accessible, False otherwise
        """
        try:
            logger.info("Testing weather API connectivity")
            result = await self.weather_handler.test_auth()
            
            if result:
                logger.info("Weather API connectivity test passed")
            else:
                logger.warning("Weather API connectivity test failed")
                
            return result
            
        except Exception as e:
            logger.error(f"Weather connectivity test failed with exception: {e}", exc_info=True)
            return False

    @activity.defn
    async def perform_preflight_check(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform preflight checks for weather operations.

        Args:
            config (Dict[str, Any]): Configuration containing parameters to test

        Returns:
            Dict[str, Any]: Preflight check results
        """
        try:
            logger.info("Performing weather preflight check")
            
            # Delegate to handler for preflight check
            result = await self.weather_handler.preflight_check(config)
            
            logger.info(f"Preflight check completed with status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Preflight check failed with exception: {e}", exc_info=True)
            return {
                "status": "failed",
                "message": f"Preflight check failed: {e}",
                "checks": {
                    "api_connectivity": False,
                    "geocoding": False,
                    "weather_data": False
                }
            } 