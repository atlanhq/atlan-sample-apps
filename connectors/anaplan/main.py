import asyncio

from app.activities import AnaplanMetadataExtractionActivities
from app.clients import AnaplanApiClient
from app.handlers import AnaplanHandler
from app.workflows import AnaplanMetadataExtractionWorkflow
from application_sdk.application import BaseApplication
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    """
    Main function for the Anaplan application.

    This sets up:
    1. Workflow client and worker (Temporal)
    2. FastAPI server with handlers
    3. Component integration (client, handler, activities)
    """

    # Initialize the application with Anaplan-specific components
    application = BaseApplication(
        name=APPLICATION_NAME,
        client_class=AnaplanApiClient,
        handler_class=AnaplanHandler,
    )

    # Setup the workflow (loads workflow client, creates activities, sets up worker)
    await application.setup_workflow(
        workflow_and_activities_classes=[
            (AnaplanMetadataExtractionWorkflow, AnaplanMetadataExtractionActivities)
        ]
    )

    # Start the worker (starts Temporal worker with workflows and activities)
    await application.start_worker()

    # Setup the application server (creates FastAPI server with handlers)
    await application.setup_server(AnaplanMetadataExtractionWorkflow)

    # Start the application server
    await application.start_server()


if __name__ == "__main__":
    asyncio.run(main())
