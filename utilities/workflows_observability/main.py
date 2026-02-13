import asyncio

from app.activities import WorkflowsObservabilityActivities
from app.handler import WorkflowsObservabilityHandler
from app.workflow import WorkflowsObservabilityWorkflow
from application_sdk.application import BaseApplication
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)

APPLICATION_NAME = "workflows-observability"


async def main():
    logger.info("Starting workflows observability application")
    # initialize application
    app = BaseApplication(
        name=APPLICATION_NAME, handler_class=WorkflowsObservabilityHandler
    )

    # setup workflow
    await app.setup_workflow(
        workflow_and_activities_classes=[
            (WorkflowsObservabilityWorkflow, WorkflowsObservabilityActivities)
        ],
    )

    # Setup the application server
    await app.setup_server(workflow_class=WorkflowsObservabilityWorkflow)

    # start worker
    await app.start_worker()

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
