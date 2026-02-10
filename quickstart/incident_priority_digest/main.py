"""Entry point for the Incident Priority Digest application."""

import asyncio

from app.activities import IncidentDigestActivities
from app.workflow import IncidentDigestWorkflow
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

APPLICATION_NAME = "incident-priority-digest"


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    logger.info("Starting incident priority digest application")

    app = BaseApplication(name=APPLICATION_NAME)

    await app.setup_workflow(
        workflow_and_activities_classes=[
            (IncidentDigestWorkflow, IncidentDigestActivities)
        ],
    )

    await app.start_worker()
    await app.setup_server(workflow_class=IncidentDigestWorkflow)
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
