"""Main entry point for simple hello world application."""

import asyncio

from app.activities import SimpleHelloActivities
from app.workflow import SimpleHelloWorkflow
from application_sdk.application import BaseApplication

APPLICATION_NAME = "simple-hello"


async def main():
    """Main function to start the application."""
    # Initialize application
    app = BaseApplication(name=APPLICATION_NAME)

    # Setup workflow
    await app.setup_workflow(
        workflow_and_activities_classes=[
            (SimpleHelloWorkflow, SimpleHelloActivities)
        ],
    )

    # Start worker
    await app.start_worker()

    # Setup the application server
    await app.setup_server(workflow_class=SimpleHelloWorkflow)

    # Start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())

