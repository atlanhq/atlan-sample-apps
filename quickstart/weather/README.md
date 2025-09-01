# Weather App ⛅

A simple weather application built using the Atlan Application SDK that fetches current weather data from [Open-Meteo](https://open-meteo.com/) - no API key required!

## Features

- **User Input**: Enter your username in the frontend
- **Weather Data**: Fetches current weather from Open-Meteo API
- **Geocoding**: Automatically resolves city names to coordinates
- **Configurable**: Supports city and temperature units via workflow args
- **Beautiful UI**: Modern, responsive frontend design

## How It Works

1. **Get workflow args** → Read city & units, with defaults if not provided
2. **Fetch weather data** → Call Open-Meteo REST API (no API key needed)
3. **Process/Format results** → Pick out temperature, weather condition, etc.
4. **Return a summary string** → e.g., "Hello Alice! Weather in London: 23°C, Clear sky"

## Default Configuration

- **City**: London
- **Units**: Celsius (supports "celsius", "fahrenheit", "metric", "imperial")
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
   poe download-components
   ```

4. Start dependencies:
   ```bash
   poe start-deps
   ```

5. Run the application:
   ```bash
   python main.py
   ```

6. Open your browser and navigate to the application (typically `http://localhost:3000`)

### Usage

1. Enter your username in the form
2. Click "Get Weather 🚀"
3. Check the Temporal UI for the workflow execution and weather summary logs

### Customizing City and Units

You can override the default city and units by including them in the POST request body:

```javascript
{
  "username": "Alice",
  "city": "Paris", 
  "units": "fahrenheit"
}
```

Supported units:
- `"celsius"` or `"metric"` → °C
- `"fahrenheit"` or `"imperial"` → °F

## API Reference

The app uses these Open-Meteo endpoints:

- **Geocoding**: `https://geocoding-api.open-meteo.com/v1/search`
- **Weather**: `https://api.open-meteo.com/v1/forecast`

## Example Output

```
Hello Alice! Weather in London, United Kingdom: 18°C, Partly cloudy
```

## Architecture

- **main.py**: Application entrypoint and setup
- **app/workflow.py**: Orchestrates the weather summary flow
- **app/activities.py**: Temporal activities that coordinate workflow execution
- **app/handler.py**: SDK interface handler for weather operations (follows HandlerInterface pattern)
- **app/client.py**: Direct API client for Open-Meteo weather services
- **frontend/**: Modern web UI for user interaction

### Component Responsibilities

- **WeatherHandler**: Provides SDK interface, handles authentication testing, preflight checks, and coordinates weather operations
- **WeatherApiClient**: Handles direct HTTP requests to Open-Meteo APIs (geocoding and weather data)
- **WeatherActivities**: Temporal activities that delegate to the handler for workflow execution
- **WeatherWorkflow**: Orchestrates the overall weather summary generation process

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