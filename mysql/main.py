"""
Main entry point for the SQL metadata extraction application.

This module initializes and runs the SQL metadata extraction application,
setting up the workflow, worker, and server components.
"""

import asyncio

from activities import SQLMetadataExtractionActivities
from application_sdk.application.metadata_extraction.sql import (
    BaseSQLMetadataExtractionApplication,
)
from application_sdk.constants import APPLICATION_NAME
from client import SQLClient
from transformer import SQLAtlasTransformer
from workflow import SQLMetadataExtractionWorkflow


async def main():
    # Initialize the application
    application = BaseSQLMetadataExtractionApplication(
        name=APPLICATION_NAME,
        client_class=SQLClient,
        transformer_class=SQLAtlasTransformer,
    )

    # Setup the workflow
    await application.setup_workflow(
        workflow_classes=[SQLMetadataExtractionWorkflow],
        activities_class=SQLMetadataExtractionActivities,
    )

    # Start the worker
    await application.start_worker()

    # Setup the application server
    await application.setup_server(
        workflow_class=SQLMetadataExtractionWorkflow,
    )

    # Start the application server
    await application.start_server()


if __name__ == "__main__":
    asyncio.run(main())
