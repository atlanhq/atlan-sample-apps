"""
Main entry point for the SQL metadata extraction application.

This module initializes and runs the SQL metadata extraction application,
setting up the workflow, worker, and server components.
"""

import asyncio

from application_sdk.application.metadata_extraction.sql import (
    BaseSQLMetadataExtractionApplication,
)
from application_sdk.common.error_codes import ApiError
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

from mysql.app.activities import SQLMetadataExtractionActivities
from mysql.app.clients import SQLClient
from mysql.app.transformer import SQLAtlasTransformer
from mysql.app.workflows import SQLMetadataExtractionWorkflow

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    try:
        # Initialize the application
        application = BaseSQLMetadataExtractionApplication(
            name=APPLICATION_NAME,
            client_class=SQLClient,
            transformer_class=SQLAtlasTransformer,
        )

        await application.setup_workflow(
            workflow_and_activities_classes=[
                (SQLMetadataExtractionWorkflow, SQLMetadataExtractionActivities)
            ],
        )

        # Start the worker
        await application.start_worker()

        # Setup the application server
        await application.setup_server(
            workflow_class=SQLMetadataExtractionWorkflow,
        )

        # Start the application server
        await application.start_server()

    except ApiError:
        logger.error(f"{ApiError.SERVER_START_ERROR}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
