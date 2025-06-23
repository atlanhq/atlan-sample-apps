import asyncio

from activities import WorkflowsObservabilityActivities
from application_sdk.application import BaseApplication
from application_sdk.observability.logger_adaptor import get_logger
from workflow import WorkflowsObservabilityWorkflow

logger = get_logger(__name__)

APPLICATION_NAME = "workflows-observability"


async def main():
    logger.info("Starting workflows observability application")
    # initialize application
    app = BaseApplication(name=APPLICATION_NAME)

    # setup workflow
    await app.setup_workflow(
        workflow_classes=[WorkflowsObservabilityWorkflow],
        activities_class=WorkflowsObservabilityActivities,
    )

    # Setup the application server
    await app.setup_server(workflow_class=WorkflowsObservabilityWorkflow)

    # start worker
    await app.start_worker()

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
