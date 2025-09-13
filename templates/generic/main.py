"""
Main entry point for the SQL metadata extraction application.

This module initializes and runs the SQL metadata extraction application,
setting up the workflow, worker, and server components.
"""

import asyncio

from app.activities import ActivitiesClass
from app.clients import ClientClass
from app.workflows import WorkflowClass
from application_sdk.application import BaseApplication
from application_sdk.common.error_codes import ApiError
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
    try:
        # TODO: Replace AppActivities with your specific activities class
        # TODO: Add your workflow classes to the list
        # TODO: Add any additional modules your workflows need
        # TODO: Register your workflow classes and endpoints
        # TODO: Add your custom initialization here

        # Initialize the application
        application = BaseApplication(name=APPLICATION_NAME, client_class=ClientClass)

        await application.setup_workflow(
            workflow_and_activities_classes=[(WorkflowClass, ActivitiesClass)],
        )

        # Start the worker
        await application.start_worker()

        # Setup the application server
        await application.setup_server(workflow_class=WorkflowClass, has_configmap=True)

        # Start the application server
        await application.start_server()

    except ApiError:
        logger.error(f"{ApiError.SERVER_START_ERROR}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
