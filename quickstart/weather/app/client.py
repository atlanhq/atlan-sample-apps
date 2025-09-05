from typing import Dict, Tuple
import requests
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


def _map_units(units: str) -> Tuple[str, str]:
    """
    Map units to Open-Meteo temperature unit and display suffix.
    
    Args:
        units (str): "celsius" or "fahrenheit"
        
    Returns:
        (str, str): (temperature_unit_query_param, display_suffix)
    """
    if units.lower() == "fahrenheit":
        return "fahrenheit", "°F"
    return "celsius", "°C"


def _wmo_code_to_text(code: int) -> str:
    """
    Convert WMO weather code to a human-readable condition text.

    Source: Open-Meteo WMO codes mapping.
    """
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return mapping.get(code, f"Weather code {code}")


class WeatherApiClient:
    """Client for Open-Meteo API interactions.
    
    Reference example showing how to handle credentials for APIs that require authentication.
    Open-Meteo doesn't require auth, but this pattern can be used for other APIs.
    """

    def __init__(self, credentials: Dict = None):
        """Initialize Weather API client.
        
        Args:
            credentials (Dict, optional): API credentials. For Open-Meteo, not required.
                Example structure for other APIs:
                {
                    "api_key": "your_api_key",
                    "base_url": "https://api.example.com",
                    "headers": {"Authorization": "Bearer token"}
                }
        """
        self.credentials = credentials or {}
        self.geocoding_base_url = "https://geocoding-api.open-meteo.com/v1"
        self.weather_base_url = "https://api.open-meteo.com/v1"
        
        # Log credential status for debugging
        if self.credentials:
            logger.debug(f"Client initialized with {len(self.credentials)} credential items")
        else:
            logger.debug("Client initialized without credentials (Open-Meteo doesn't require auth)")

    async def geocode_city(self, city: str) -> Tuple[float, float, str]:
        """
        Resolve a city name to coordinates and resolved name.

        Args:
            city (str): The city name to geocode

        Returns:
            Tuple[float, float, str]: (latitude, longitude, resolved_city_name)

        Raises:
            ValueError: If the city cannot be resolved.
        """
        url = f"{self.geocoding_base_url}/search"
        params = {"name": city, "count": 1, "language": "en", "format": "json"}
        
        # Example of how to use credentials for APIs that need them
        headers = self.credentials.get("headers", {})
        
        try:
            logger.debug(f"Geocoding city: {city}")
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            results = data.get("results", [])
            if not results:
                raise ValueError(f"Could not find coordinates for city '{city}'")
                
            top = results[0]
            lat = float(top["latitude"])
            lon = float(top["longitude"])
            resolved = f"{top.get('name', city)}{', ' + top['country'] if top.get('country') else ''}"
            
            logger.info(f"Geocoded '{city}' -> ({lat}, {lon}) as '{resolved}'")
            return lat, lon, resolved
            
        except Exception as e:
            logger.error(f"Geocoding failed for '{city}': {e}")
            raise

    async def fetch_current_weather(
        self, lat: float, lon: float, temp_unit: str
    ) -> Tuple[float, int]:
        """
        Fetch current weather for the given coordinates.

        Args:
            lat (float): Latitude
            lon (float): Longitude  
            temp_unit (str): Temperature unit ("celsius" or "fahrenheit")

        Returns:
            Tuple[float, int]: (temperature_value, wmo_weather_code)

        Raises:
            ValueError: If the API response is invalid.
        """
        url = f"{self.weather_base_url}/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "temperature_unit": temp_unit,
        }
        
        # Example of how to use credentials for APIs that need them
        headers = self.credentials.get("headers", {})
        
        try:
            logger.debug(f"Fetching weather for coordinates ({lat}, {lon})")
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            current = data.get("current_weather", {})
            if "temperature" not in current or "weathercode" not in current:
                raise ValueError("Invalid Open-Meteo response: missing current weather")
                
            temperature = float(current["temperature"])
            weather_code = int(current["weathercode"])
            
            logger.info(f"Fetched weather: {temperature}° ({temp_unit}), code={weather_code}")
            return temperature, weather_code
            
        except Exception as e:
            logger.error(f"Weather fetch failed for ({lat}, {lon}): {e}")
            raise

    async def get_weather_summary(self, username: str, city: str, units: str) -> str:
        """
        Build a friendly weather summary for the provided user and city.

        Args:
            username (str): Name of the user to greet
            city (str): City name to look up
            units (str): "celsius" or "fahrenheit"

        Returns:
            str: Summary string, e.g., "Hello Alice! Weather in London: 23°C, Clear sky"
        """
        temp_unit, display_suffix = _map_units(units)

        # Step 1: Geocode the city to lat/lon
        lat, lon, resolved_city = await self.geocode_city(city)

        # Step 2: Fetch current weather for coordinates
        temperature, weather_code = await self.fetch_current_weather(lat, lon, temp_unit)
        condition = _wmo_code_to_text(weather_code)

        # Step 3: Format the summary
        summary = (
            f"Hello {username}! Weather in {resolved_city}: "
            f"{temperature}{display_suffix}, {condition}"
        )
        
        logger.info(f"Generated weather summary: {summary}")
        return summary 