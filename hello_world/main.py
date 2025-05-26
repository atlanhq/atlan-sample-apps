import asyncio

from activities import HelloWorldActivities
from application_sdk.application import BaseApplication
from application_sdk.common.logger_adaptors import get_logger
from workflow import HelloWorldWorkflow

logger = get_logger(__name__)

APPLICATION_NAME = "hello-world"


async def main():
    logger.info("Starting hello world application")
    # initialize application
    app = BaseApplication(name=APPLICATION_NAME)

    # setup workflow
    await app.setup_workflow(
        workflow_classes=[HelloWorldWorkflow],
        activities_class=HelloWorldActivities,
    )

    # start worker
    await app.start_worker()

    # Setup the application server
    await app.setup_server(workflow_class=HelloWorldWorkflow)

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
