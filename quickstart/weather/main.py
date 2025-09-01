import asyncio
from typing import Any, Dict

from app.activities import WeatherActivities
from app.workflow import WeatherWorkflow
from app.handler import WeatherHandler
from app.client import WeatherApiClient
from application_sdk.application import BaseApplication
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

APPLICATION_NAME = "weather"

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


@observability(logger=logger, metrics=metrics, traces=traces)
async def main(daemon: bool = True) -> Dict[str, Any]:
    """
    Application entrypoint for the Weather app.

    - Initializes the application runtime
    - Registers the workflow and activities
    - Starts the worker and HTTP server
    """
    logger.info("Starting weather application")

    # initialize application
    app = BaseApplication(name=APPLICATION_NAME, handlerWeatherHandler)

    # setup workflow (include requests as passthrough for the activity sandbox)
    await app.setup_workflow(
        workflow_and_activities_classes=[(WeatherWorkflow, WeatherActivities)],
        passthrough_modules=["requests", "urllib3"],
    )

    # start worker
    await app.start_worker()

    # Setup the application server
    await app.setup_server(workflow_class=WeatherWorkflow)

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main(daemon=False)) 