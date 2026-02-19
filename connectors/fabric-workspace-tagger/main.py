"""Main entry point for the Microsoft Fabric Workspace Tagger app.

This application synchronizes workspace metadata and tags from Microsoft Fabric
/ Power BI to Atlan, enabling governance and cost management use cases.
"""

import asyncio

from app.activities import FabricWorkspaceTaggerActivities
from app.workflow import FabricWorkspaceTagSyncWorkflow
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

APPLICATION_NAME = "fabric-workspace-tagger"


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    """Initialize and start the Fabric Workspace Tagger application.

    This function:
    1. Creates the base application instance
    2. Sets up the workflow and activities
    3. Starts the Temporal worker
    4. Sets up and starts the API server for workflow execution

    The application will be available at http://localhost:8000
    """
    logger.info("Starting Microsoft Fabric Workspace Tagger application")

    try:
        # Initialize application
        app = BaseApplication(name=APPLICATION_NAME)

        # Setup workflow with activities
        logger.info("Setting up workflow and activities")
        await app.setup_workflow(
            workflow_and_activities_classes=[
                (FabricWorkspaceTagSyncWorkflow, FabricWorkspaceTaggerActivities)
            ],
        )

        # Start the Temporal worker
        logger.info("Starting Temporal worker...")
        await app.start_worker()

        # Setup the application server
        logger.info("Setting up API server...")
        await app.setup_server(workflow_class=FabricWorkspaceTagSyncWorkflow)

        # Start the server
        logger.info("Starting API server on port 8000...")
        await app.start_server()

        logger.info("Application started successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
