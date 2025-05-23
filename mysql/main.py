"""
Main entry point for the SQL metadata extraction application.

This module initializes and runs the SQL metadata extraction application,
setting up the workflow, worker, and server components.
"""

import asyncio

from activities import SQLMetadataExtractionActivities
from application_sdk.application.metadata_extraction.sql import (
    BaseSQLMetadataExtractionApplication,
)
from application_sdk.common.error_codes import ApiError
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import MetricType, get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from client import SQLClient
from transformer import SQLAtlasTransformer
from workflow import SQLMetadataExtractionWorkflow

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


async def main():
    try:
        logger.info("Starting SQL metadata extraction application")

        # Record application startup metric
        metrics.record_metric(
            name="sql_metadata_extraction_application_startup",
            value=1.0,
            metric_type=MetricType.COUNTER,
            labels={"application_name": APPLICATION_NAME, "status": "started"},
            description="SQL metadata extraction application startup counter",
            unit="count",
        )

        # Record trace for application startup
        traces.record_trace(
            name="sql_metadata_extraction_application_startup",
            trace_id="app_startup",
            span_id="main",
            kind="INTERNAL",
            status_code="OK",
            attributes={
                "application_name": APPLICATION_NAME,
                "service.name": "sql-metadata-extraction",
                "service.version": "1.0.0",
            },
        )

        # Initialize the application
        application = BaseSQLMetadataExtractionApplication(
            name=APPLICATION_NAME,
            client_class=SQLClient,
            transformer_class=SQLAtlasTransformer,
        )

        # Setup the workflow
        await application.setup_workflow(
            workflow_classes=[SQLMetadataExtractionWorkflow],
            activities_class=SQLMetadataExtractionActivities,
        )

        # Start the worker
        await application.start_worker()

        # Setup the application server
        await application.setup_server(
            workflow_class=SQLMetadataExtractionWorkflow,
        )

        # Record server setup metric
        metrics.record_metric(
            name="sql_metadata_extraction_server_setup",
            value=1.0,
            metric_type=MetricType.COUNTER,
            labels={"application_name": APPLICATION_NAME, "status": "ready"},
            description="SQL metadata extraction server setup counter",
            unit="count",
        )

        # Start the application server
        await application.start_server()

    except Exception as e:
        logger.error(
            "Application startup failed",
            extra={
                "error_code": ApiError.SERVER_START_ERROR.code,
                "error": str(e),
            },
        )
        raise ApiError.SERVER_START_ERROR


if __name__ == "__main__":
    asyncio.run(main())
