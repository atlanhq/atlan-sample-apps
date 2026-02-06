import asyncio

from application_sdk.application.metadata_extraction.sql import (
    BaseSQLMetadataExtractionApplication,
)
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.transformers.query import QueryBasedTransformer

from app.clients import SQLClient

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    # Initialize the application
    application = BaseSQLMetadataExtractionApplication(
        name=APPLICATION_NAME,
        client_class=SQLClient,
        transformer_class=QueryBasedTransformer,  # type: ignore
    )

    # Setup the workflow
    await application.setup_workflow()

    # Start the worker
    await application.start_worker()

    # Setup the application server
    await application.setup_server()

    # Start the application server
    await application.start_server()


if __name__ == "__main__":
    asyncio.run(main())
