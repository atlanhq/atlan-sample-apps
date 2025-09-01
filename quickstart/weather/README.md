# Weather App ⛅

A simple weather application built using the Atlan Application SDK that fetches current weather data from [Open-Meteo](https://open-meteo.com/) - no API key required!

## Features

- **User Input**: Enter username, city, and temperature units in the frontend
- **Weather Data**: Fetches current weather from Open-Meteo API
- **Geocoding**: Automatically resolves city names to coordinates
- **Configurable**: Supports city and temperature units via frontend or workflow args
- **Beautiful UI**: Modern, responsive frontend design
- **Reference Pattern**: Demonstrates credentials handling for APIs that require authentication

## How It Works

1. **User Input** → Frontend collects username, city, and temperature units
2. **Get workflow args** → Merge user input with defaults (city: London, units: celsius)
3. **Fetch weather data** → Call Open-Meteo REST API (no API key needed)
4. **Process/Format results** → Extract temperature, weather condition, etc.
5. **Return a summary string** → e.g., "Hello Alice! Weather in Paris: 23°F, Clear sky"

## Default Configuration

- **City**: London (can be overridden via frontend)
- **Units**: Celsius (supports "celsius" or "fahrenheit")
- **Username**: From frontend input (required)

## Getting Started

### Prerequisites

- Python 3.11+
- UV or pip for dependency management
- Temporal and Dapr (handled by poe tasks)

### Installation

1. Navigate to the weather app directory:
   ```bash
   cd quickstart/weather
   ```

2. Install dependencies:
   ```bash
   uv sync
   # or
   pip install -e .
   ```

3. Download components (optional):
   ```bash
   uv run poe download-components
   ```

4. Start dependencies:
   ```bash
   uv run poe start-deps
   ```

5. Run the application:
   ```bash
   python main.py
   # or
   uv run main.py
   ```

6. Open your browser and navigate to the application (typically `http://localhost:3000`)

### Usage

1. **Enter your username** (required)
2. **Optionally enter a city** (defaults to London if empty)
3. **Select temperature units** (Celsius or Fahrenheit)
4. **Click "Get Weather 🚀"**
5. **Check the Temporal UI** for the workflow execution and weather summary logs


### Customizing City and Units

You can override the default city and units via:

**Frontend Form:**
- Enter city name in the city field
- Select temperature units from the dropdown

**API Request:**
```javascript
{
  "username": "Alice",
  "city": "Paris", 
  "units": "fahrenheit"
}
```

**Supported Units:**
- `"celsius"` → °C
- `"fahrenheit"` → °F

## API Reference

The app uses these Open-Meteo endpoints:

- **Geocoding**: `https://geocoding-api.open-meteo.com/v1/search`
- **Weather**: `https://api.open-meteo.com/v1/forecast`

## Example Output

```
Hello Alice! Weather in Paris, France: 23°F, Clear sky
```

## Architecture

- **main.py**: Application entrypoint and setup
- **app/workflow.py**: Orchestrates the weather summary flow
- **app/activities.py**: Temporal activities that coordinate workflow execution
- **app/handler.py**: SDK interface handler for weather operations (follows HandlerInterface pattern)
- **app/client.py**: Direct API client for Open-Meteo weather services with credentials pattern
- **frontend/**: Modern web UI for user interaction

### Component Responsibilities

- **WeatherHandler**: Provides SDK interface, handles authentication testing, preflight checks, and coordinates weather operations
- **WeatherApiClient**: Handles direct HTTP requests to Open-Meteo APIs with credentials support for reference
- **WeatherActivities**: Temporal activities that handle workflow args and delegate to the handler
- **WeatherWorkflow**: Orchestrates the overall weather summary generation process

### Credentials Pattern

The app demonstrates a credentials handling pattern for APIs that require authentication:

```python
# Example usage for APIs with authentication
credentials = {
    "api_key": "your_api_key",
    "headers": {"Authorization": "Bearer token"}
}
client = WeatherApiClient(credentials)
```

While Open-Meteo doesn't require authentication, this pattern serves as a reference for other apps.

## Development

### Available Tasks

```bash
poe start-deps     # Start Temporal and Dapr
poe stop-deps      # Stop dependencies
poe start-dapr     # Start Dapr only
poe start-temporal # Start Temporal only
```

### Logging

Weather summaries are logged at the workflow level. View them in:
- Temporal UI: `http://localhost:8233`
- Application logs in your terminal

## License

Apache-2.0 