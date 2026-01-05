import asyncio

from app import register_routes
from app.activities import DqPocActivities
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

    # Setup the application server (default SDK server)
    await app.setup_server(workflow_class=DqPocWorkflow)

    # Add custom routes onto the default server
    register_routes.register_custom_routes(  # type: ignore[arg-type]
        app.server
    )

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
