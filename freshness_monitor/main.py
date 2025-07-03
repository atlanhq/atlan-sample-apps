import asyncio

from app.activities import FreshnessMonitorActivities
from app.workflows import FreshnessMonitorWorkflow
from application_sdk.application import BaseApplication
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)

APPLICATION_NAME = "freshness-monitor"


async def main():
    # Initialize application
    app = BaseApplication(name=APPLICATION_NAME)

    # Setup workflow and worker
    await app.setup_workflow(
        workflow_and_activities_classes=[
            (FreshnessMonitorWorkflow, FreshnessMonitorActivities)
        ],
    )
    await app.start_worker()

    # Setup server
    await app.setup_server(workflow_class=FreshnessMonitorWorkflow)

    # Start the API server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
