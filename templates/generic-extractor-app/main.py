"""
Atlan Connector Template - Application Entry Point

This is the main entry point for the connector application.
It initializes the Temporal workflow system and FastAPI server.
"""

import asyncio

from app.activities import ConnectorActivities
from app.clients import ConnectorClient
from app.handlers import ConnectorHandler
from app.workflows import ConnectorWorkflow
from application_sdk.application import BaseApplication
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.decorators.observability_decorator import observability
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    """Initialize and start the connector application."""

    # Create application with your custom components
    application = BaseApplication(
        name=APPLICATION_NAME,
        client_class=ConnectorClient,
        handler_class=ConnectorHandler,
    )

    # Setup workflow with activities
    await application.setup_workflow(
        workflow_and_activities_classes=[(ConnectorWorkflow, ConnectorActivities)]
    )

    # Start the Temporal worker
    await application.start_worker()

    # Setup and start the FastAPI server
    await application.setup_server(workflow_class=ConnectorWorkflow, has_configmap=True)
    await application.start_server()


if __name__ == "__main__":
    asyncio.run(main())
