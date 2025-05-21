from application_sdk.activities import ActivitiesInterface
from application_sdk.common.error_codes import ActivityError, ClientError, TemporalError
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger
activity.traces = get_traces()
activity.metrics = get_metrics()


class HelloWorldActivities(ActivitiesInterface):
    @activity.defn
    async def say_hello(self, name: str) -> str:
        try:
            if not name or not isinstance(name, str):
                logger.error(
                    "Invalid name parameter",
                    extra={"error_code": ClientError.INPUT_VALIDATION_ERROR.code},
                )
                raise ClientError.INPUT_VALIDATION_ERROR

            activity.logger.info(f"Saying hello to {name}")

            # Record metric for activity execution
            activity.metrics.record_metric(
                name="hello_world_activity_execution",
                value=1.0,
                metric_type="counter",
                labels={"activity_type": "say_hello", "name": name},
                description="Number of times say_hello activity is executed",
                unit="count",
            )

            # Add trace for activity execution
            with activity.traces.record_trace(
                name="say_hello_activity",
                trace_id=activity.info().workflow_id,
                span_id=activity.info().activity_id,
                kind="INTERNAL",
                status_code="OK",
                attributes={
                    "workflow_id": activity.info().workflow_id,
                    "activity_id": activity.info().activity_id,
                    "name": name,
                    "activity_type": "say_hello",
                },
            ):
                try:
                    return f"Hello, {name}!"
                except Exception as e:
                    logger.error(
                        "Failed to generate greeting",
                        extra={
                            "error_code": ActivityError.ACTIVITY_END_ERROR.code,
                            "error": str(e),
                        },
                    )
                    raise ActivityError.ACTIVITY_END_ERROR

        except Exception as e:
            logger.error(
                "Activity execution failed",
                extra={
                    "error_code": TemporalError.TEMPORAL_CLIENT_ACTIVITY_ERROR.code,
                    "error": str(e),
                },
            )
            raise TemporalError.TEMPORAL_CLIENT_ACTIVITY_ERROR
