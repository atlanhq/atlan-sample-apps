import asyncio
from typing import Any, Dict

from app.activities import ExtractorActivities
from app.workflow import ExtractorWorkflow
from app.handler import ExtractorHandler
from app.client import ExtractorClient
from application_sdk.application import BaseApplication
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

APPLICATION_NAME = "extractor"

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


@observability(logger=logger, metrics=metrics, traces=traces)
async def main(daemon: bool = True) -> Dict[str, Any]:
    """
    Application entrypoint for the Extractor app.

    - Initializes the application runtime
    - Registers the workflow and activities
    - Starts the worker and HTTP server
    """
    logger.info("Starting extractor application")

    # initialize application
    app = BaseApplication(
        name=APPLICATION_NAME,
        client_class=ExtractorClient,
        handler_class=ExtractorHandler,
    )

    # setup workflow (include requests as passthrough for the activity sandbox)
    await app.setup_workflow(
        workflow_and_activities_classes=[(ExtractorWorkflow, ExtractorActivities)],
        passthrough_modules=["requests", "urllib3"],
    )

    # start worker
    await app.start_worker()

    # Setup the application server
    await app.setup_server(workflow_class=ExtractorWorkflow)

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main(daemon=False))
