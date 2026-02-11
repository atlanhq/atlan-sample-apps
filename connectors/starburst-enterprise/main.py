"""
Main entry point for the Starburst Enterprise (SEP) metadata extraction application.

This connector uses a hybrid extraction approach:
- REST API: Data Products, Domains, Datasets, Dataset Columns
- SQL (INFORMATION_SCHEMA): Catalogs, Schemas, Tables, Views, Columns
"""

import asyncio

from app.activities import SEPMetadataExtractionActivities
from app.handler import SEPHandler
from app.sql_client import SEPSQLClient
from app.transformer import SEPAtlasTransformer
from app.workflows import SEPMetadataExtractionWorkflow
from application_sdk.application import BaseApplication
from application_sdk.common.error_codes import ApiError
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    try:
        application = BaseApplication(
            name=APPLICATION_NAME,
            client_class=SEPSQLClient,
            handler_class=SEPHandler,
            transformer_class=SEPAtlasTransformer,
        )

        await application.setup_workflow(
            workflow_and_activities_classes=[
                (SEPMetadataExtractionWorkflow, SEPMetadataExtractionActivities)
            ],
        )

        # Start the Temporal worker
        await application.start_worker()

        # Setup and start the FastAPI server
        await application.setup_server(
            workflow_class=SEPMetadataExtractionWorkflow,
        )
        await application.start_server()

    except ApiError:
        logger.error(f"{ApiError.SERVER_START_ERROR}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
