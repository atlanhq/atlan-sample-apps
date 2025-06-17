import asyncio
import os

from app.activities import AssetDescriptionReminderActivities
from app.application import AssetDescriptionReminderApplication
from app.clients import AssetDescriptionClient
from app.handlers import AssetDescriptionHandler
from app.workflows import AssetDescriptionReminderWorkflow
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)

APPLICATION_NAME = "asset-description-reminder"


async def main():
    # Initialize application with loaded client
    app = AssetDescriptionReminderApplication(name=APPLICATION_NAME)

    # Setup workflow with activities factory that uses same client
    await app.setup_workflow(
        workflow_classes=[AssetDescriptionReminderWorkflow],
        activities_class=AssetDescriptionReminderActivities,
    )

    # Start worker
    await app.start_worker()

    logger.info("Setting up server...")
    await app.setup_server(workflow_class=AssetDescriptionReminderWorkflow)
    logger.info("Server setup complete")

    logger.info("Setting up API routes...")
    await app.setup_api_server()
    logger.info("API routes setup complete")

    # Start server
    logger.info("Starting server...")
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
