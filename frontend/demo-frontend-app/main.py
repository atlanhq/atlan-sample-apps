import asyncio

from application_sdk.application import BaseApplication
from application_sdk.server.fastapi import APIServer
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()

APPLICATION_NAME = "demo-frontend"


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    logger.info("Starting demo-frontend application")
    
    # define a basic server instance with no strings attached
    basicServer = APIServer()

    # initialize application
    app = BaseApplication(name=APPLICATION_NAME,server=basicServer)

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
