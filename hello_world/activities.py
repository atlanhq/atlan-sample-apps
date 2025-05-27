from application_sdk.activities import ActivitiesInterface
from application_sdk.common.error_codes import (
    ActivityError,
    ClientError,
    OrchestratorError,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import TracingContext, get_traces
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger
activity.traces = get_traces()
activity.metrics = get_metrics()


class HelloWorldActivities(ActivitiesInterface):
    @activity.defn
    async def say_hello(self, name: str) -> str:
        # Create tracing context for this activity
        tracing = TracingContext(
            logger=activity.logger,
            metrics=activity.metrics,
            traces=activity.traces,
            trace_id=activity.info().workflow_id,
            parent_span_id=activity.info().activity_id,
        )

        try:
            if not name or not isinstance(name, str):
                logger.error(
                    "Invalid name parameter",
                    extra={"error_code": ClientError.INPUT_VALIDATION_ERROR.code},
                )
                raise ClientError.INPUT_VALIDATION_ERROR

            activity.logger.info(f"Saying hello to {name}")

            # Use tracing context for the activity execution
            async with tracing.trace_operation(
                operation_name="say_hello_activity",
                description=f"Executing say_hello activity for {name}",
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
                    "error_code": OrchestratorError.TEMPORAL_CLIENT_ACTIVITY_ERROR.code,
                    "error": str(e),
                },
            )
            raise OrchestratorError.TEMPORAL_CLIENT_ACTIVITY_ERROR
