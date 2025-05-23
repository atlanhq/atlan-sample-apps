import asyncio

from activities import HelloWorldActivities
from application_sdk.application import BaseApplication
from application_sdk.common.error_codes import ApiError
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import MetricType, get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from workflow import HelloWorldWorkflow

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()

APPLICATION_NAME = "hello-world"


async def main():
    try:
        logger.info("Starting hello world application")

        # Record application startup metric
        metrics.record_metric(
            name="hello_world_application_startup",
            value=1.0,
            metric_type=MetricType.COUNTER,
            labels={"application_name": APPLICATION_NAME, "status": "started"},
            description="Application startup counter",
            unit="count",
        )

        # Record trace for application startup
        traces.record_trace(
            name="hello_world_application_startup",
            trace_id="app_startup",
            span_id="main",
            kind="INTERNAL",
            status_code="OK",
            attributes={
                "application_name": APPLICATION_NAME,
                "service.name": APPLICATION_NAME,
                "service.version": "1.0.0",
            },
        )

        # initialize application
        app = BaseApplication(name=APPLICATION_NAME)

        # setup workflow
        await app.setup_workflow(
            workflow_classes=[HelloWorldWorkflow],
            activities_class=HelloWorldActivities,
        )

        # start worker
        await app.start_worker()

        # Setup the application server
        await app.setup_server(workflow_class=HelloWorldWorkflow)

        # Record server setup metric
        metrics.record_metric(
            name="hello_world_server_setup",
            value=1.0,
            metric_type=MetricType.COUNTER,
            labels={"application_name": APPLICATION_NAME, "status": "ready"},
            description="Server setup counter",
            unit="count",
        )

        # start server
        await app.start_server()

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
