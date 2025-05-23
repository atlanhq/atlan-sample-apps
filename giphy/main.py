import asyncio
from typing import Any, Dict

from activities import GiphyActivities
from application_sdk.application import BaseApplication
from application_sdk.observability.logger_adaptor import get_logger
from workflow import GiphyWorkflow

APPLICATION_NAME = "giphy"

logger = get_logger(__name__)


async def main(daemon: bool = True) -> Dict[str, Any]:
    logger.info("Starting giphy application")

    # initialize application
    app = BaseApplication(name=APPLICATION_NAME)

    # setup workflow
    await app.setup_workflow(
        workflow_classes=[GiphyWorkflow],
        activities_class=GiphyActivities,
        passthrough_modules=["requests", "urllib3"],
    )

    # start worker
    await app.start_worker()

    # Setup the application server
    await app.setup_server(workflow_class=GiphyWorkflow)

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main(daemon=False))
