import asyncio
from typing import Any, Dict

from app.activities import AIGiphyActivities
from app.workflow import AIGiphyWorkflow
from application_sdk.application import BaseApplication
from application_sdk.observability.logger_adaptor import get_logger

APPLICATION_NAME = "ai-giphy"

logger = get_logger(__name__)


async def main(daemon: bool = True) -> Dict[str, Any]:
    logger.info("Starting giphy application")

    # initialize application
    app = BaseApplication(name=APPLICATION_NAME)

    # setup workflow
    await app.setup_workflow(
        workflow_and_activities_classes=[(AIGiphyWorkflow, AIGiphyActivities)],
        passthrough_modules=[
            "requests",
            "urllib3",
            "httpx",
            "urllib.request",
            "langchain_openai",
            "langchain_core",
            "langchain",
            "langchainhub",
            "warnings",
            "os",
            "grpc",
        ],
    )

    # start worker
    await app.start_worker()
    await app.setup_server(workflow_class=AIGiphyWorkflow)

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main(daemon=True))
