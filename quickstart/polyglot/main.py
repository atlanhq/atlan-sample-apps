"""Main entry point for the Polyglot sample app.

This application demonstrates how to integrate Python and Java code using JPype
within an Atlan Application SDK workflow. It showcases calling Java methods
from Python activities and workflows.
"""

import asyncio

from app.activities import PolyglotActivities
from app.workflow import PolyglotWorkflow
from application_sdk.application import BaseApplication
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()

APPLICATION_NAME = "polyglot"


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    """Initialize and start the Polyglot application.

    This function:
    1. Creates the base application instance
    2. Sets up the workflow and activities
    3. Starts the Temporal worker
    4. Sets up and starts the API server

    The application will be available at http://localhost:8000
    """
    logger.info("Starting Polyglot application")

    try:
        # Initialize application
        app = BaseApplication(name=APPLICATION_NAME)

        # Setup workflow with activities
        await app.setup_workflow(
            workflow_and_activities_classes=[(PolyglotWorkflow, PolyglotActivities)],
        )

        # Start the Temporal worker
        logger.info("Starting Temporal worker...")
        await app.start_worker()

        # Setup the application server
        logger.info("Setting up API server...")
        await app.setup_server(workflow_class=PolyglotWorkflow)

        # Start the server
        logger.info("Starting API server on port 8000...")
        await app.start_server()

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
