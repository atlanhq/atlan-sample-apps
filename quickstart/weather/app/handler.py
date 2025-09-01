from typing import Any, Dict

from application_sdk.handlers import HandlerInterface
from application_sdk.observability.logger_adaptor import get_logger

from app.client import WeatherApiClient, _map_units

logger = get_logger(__name__)


class WeatherHandler(HandlerInterface):
    """Weather app handler for Atlan SDK interactions.
    
    This handler provides the SDK interface for weather data operations,
    coordinating between the frontend, SDK, and the WeatherApiClient.
    
    CALL CHAIN: Frontend --> SDK --> WeatherHandler --> WeatherApiClient --> Open-Meteo API
    
    SDK BEHAVIOR: Base handler automatically calls load() with credentials before calling any method,
    then wraps responses in standard format ({"success": true/false, "data": ...})
    """

    def __init__(self, weather_client: WeatherApiClient | None = None):
        """Initialize Weather handler with optional client instance.

        Args:
            weather_client (Optional[WeatherApiClient]): Optional WeatherApiClient instance
        """
        self.weather_client = weather_client or WeatherApiClient()

    # ============================================================================
    # SECTION 1: SDK INTERFACE METHODS (Called by FastAPI endpoints)
    # ============================================================================

    async def load(self, credentials: Dict[str, Any]) -> None:
        """SDK interface: Initialize Weather client with credentials.
        
        For Open-Meteo API, no authentication is required, but we store
        any provided configuration for potential future use.

        Args:
            credentials (Dict[str, Any]): Configuration dict (not required for Open-Meteo)
        """
        if self.weather_client:
            self.weather_client.credentials = credentials
            logger.debug("Loaded credentials for Weather client (Open-Meteo requires no auth)")

    async def test_auth(self) -> bool:
        """SDK interface: Test Weather API connectivity.
        
        Since Open-Meteo requires no authentication, we test connectivity
        by making a simple geocoding request.

        Returns:
            bool: True if API is accessible, False otherwise
        """
        try:
            if not self.weather_client:
                raise Exception("Weather client not initialized")

            # Test connectivity with a simple geocoding request
            logger.debug("Testing Open-Meteo API connectivity")
            await self.weather_client.geocode_city("London")
            
            logger.info("Weather API connectivity test successful")
            return True
            
        except Exception as e:
            logger.error(f"Weather API connectivity test failed: {e}")
            return False

    async def fetch_metadata(self, metadata_type: str = "weather", database: str = "") -> Dict[str, Any]:
        """SDK interface: Fetch weather metadata (not applicable for weather app).
        
        This method exists to satisfy the HandlerInterface but is not used
        in the weather app context.

        Args:
            metadata_type (str): Type of metadata to fetch (ignored)
            database (str): Database name (ignored)

        Returns:
            Dict[str, Any]: Empty response indicating this operation is not supported
        """
        logger.warning("fetch_metadata called on WeatherHandler - operation not supported")
        return {
            "message": "Metadata fetching not applicable for weather data",
            "supported_operations": ["get_weather_summary"]
        }

    async def preflight_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """SDK interface: Perform preflight checks for weather operations.

        Args:
            payload (Dict[str, Any]): Request payload containing operation parameters

        Returns:
            Dict[str, Any]: Preflight check results
        """
        try:
            logger.info("Performing weather API preflight check")
            
            # Extract parameters
            city = payload.get("city", "London")
            units = payload.get("units", "celsius")
            
            # Test API connectivity
            connectivity_ok = await self.test_auth()
            if not connectivity_ok:
                return {
                    "status": "failed",
                    "message": "Failed to connect to Open-Meteo API",
                    "checks": {
                        "api_connectivity": False,
                        "geocoding": False,
                        "weather_data": False
                    }
                }

            # Test geocoding for the specified city
            try:
                lat, lon, resolved_city = await self.weather_client.geocode_city(city)
                geocoding_ok = True
                geocoding_message = f"Successfully resolved '{city}' to '{resolved_city}'"
            except Exception as e:
                geocoding_ok = False
                geocoding_message = f"Failed to geocode city '{city}': {e}"

            # Test weather data fetching if geocoding succeeded
            weather_ok = False
            weather_message = "Skipped due to geocoding failure"
            
            if geocoding_ok:
                try:
                    temp_unit, _ = _map_units(units)
                    temperature, weather_code = await self.weather_client.fetch_current_weather(
                        lat, lon, temp_unit
                    )
                    weather_ok = True
                    weather_message = f"Successfully fetched weather data: {temperature}°, code {weather_code}"
                except Exception as e:
                    weather_message = f"Failed to fetch weather data: {e}"

            overall_status = "passed" if all([connectivity_ok, geocoding_ok, weather_ok]) else "failed"
            
            return {
                "status": overall_status,
                "message": f"Preflight check {overall_status}",
                "checks": {
                    "api_connectivity": connectivity_ok,
                    "geocoding": geocoding_ok,
                    "weather_data": weather_ok
                },
                "details": {
                    "geocoding_message": geocoding_message,
                    "weather_message": weather_message,
                    "tested_city": city,
                    "tested_units": units
                }
            }
            
        except Exception as e:
            logger.error(f"Preflight check failed with unexpected error: {e}", exc_info=True)
            return {
                "status": "failed",
                "message": f"Preflight check failed: {e}",
                "checks": {
                    "api_connectivity": False,
                    "geocoding": False,
                    "weather_data": False
                }
            }

    # ============================================================================
    # SECTION 2: WEATHER-SPECIFIC METHODS
    # ============================================================================

    async def get_weather_summary(self, username: str, city: str = "London", units: str = "celsius") -> str:
        """Get a friendly weather summary for the specified user and location.

        Args:
            username (str): Name of the user to greet
            city (str): City name for weather lookup (default: "London")
            units (str): Temperature units (default: "celsius")

        Returns:
            str: Formatted weather summary string

        Raises:
            Exception: If weather data cannot be retrieved
        """
        try:
            logger.info(f"Getting weather summary for user '{username}' in '{city}' using '{units}' units")
            
            if not self.weather_client:
                raise Exception("Weather client not initialized")

            summary = await self.weather_client.get_weather_summary(username, city, units)
            
            logger.info(f"Successfully generated weather summary: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get weather summary: {e}", exc_info=True)
            raise 