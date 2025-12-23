import asyncio

from app.activities import DqPocActivities
from app.custom_server import DqPocServer
from app.workflow import DqPocWorkflow
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

APPLICATION_NAME = "dq-poc"


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    logger.info("Starting dq poc sample application")
    # initialize application
    app = BaseApplication(name=APPLICATION_NAME)

    # setup workflow
    await app.setup_workflow(
        workflow_and_activities_classes=[(DqPocWorkflow, DqPocActivities)],
    )

    # start worker
    await app.start_worker()

    # Setup the application server (custom endpoint + default SDK endpoints)
    server = DqPocServer(
        workflow_client=app.workflow_client,
        handler=app.handler_class(client=app.client_class()),
    )
    server.register_default_workflow_start(workflow_class=DqPocWorkflow)
    app.server = server

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
