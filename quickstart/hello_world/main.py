import asyncio
import os
from typing import Any, Dict

from app.activities import HelloWorldActivities
from app.workflow import HelloWorldWorkflow
from application_sdk.application import BaseApplication
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from fastapi import Request
from temporalio.client import Client

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()

APPLICATION_NAME = "hello-world"


def register_kafka_listener(app: BaseApplication):
    """
    Register Kafka listener endpoint to trigger Temporal workflow.
    """
    # Get the FastAPI app from the application server
    fastapi_app = app.server.app

    # Define Dapr subscription endpoint
    async def subscribe():
        """
        Dapr calls this endpoint to discover which topics this app subscribes to.
        """
        subscriptions = [
            {
                "pubsubname": "kafka-pubsub",
                "topic": "airflow-openlineage",
                "route": "/kafka-events",
            }
        ]
        logger.info(
            f"Dapr subscription discovery called. Returning subscriptions: {subscriptions}"
        )
        return subscriptions

    # Remove existing route and add new one
    fastapi_app.router.routes = [
        route
        for route in fastapi_app.router.routes
        if not (hasattr(route, "path") and route.path == "/dapr/subscribe")
    ]
    fastapi_app.add_api_route("/dapr/subscribe", subscribe, methods=["GET"])

    # Register Kafka event handler endpoint
    @fastapi_app.post("/kafka-events")
    async def handle_kafka_event(request: Request):
        """
        Handle incoming Kafka events from Dapr and trigger Temporal workflow.
        """
        try:
            # Get the event data
            body = await request.json()

            logger.info("=" * 80)
            logger.info("KAFKA EVENT RECEIVED")
            logger.info("=" * 80)
            logger.info(f"Full event data: {body}")

            # Extract the actual message data
            message_data = body.get("data", {})
            logger.info(f"Message data: {message_data}")

            # Extract name from message or use default
            name = (
                message_data.get("name", "World")
                if isinstance(message_data, dict)
                else "World"
            )

            # Prepare workflow configuration
            workflow_config: Dict[str, Any] = {"workflow_args": {"name": name}}

            # Trigger the Temporal workflow
            # Connect to Temporal server
            temporal_url = os.getenv("TEMPORAL_HOST_URL", "localhost:7233")
            temporal_client = await Client.connect(temporal_url)

            workflow_id = f"hello-world-kafka-{asyncio.get_event_loop().time()}"

            logger.info(f"Triggering Temporal workflow with ID: {workflow_id}")

            # Use the same task queue that the worker is using
            task_queue = f"atlan-{APPLICATION_NAME}-local"

            await temporal_client.start_workflow(
                HelloWorldWorkflow.run,
                workflow_config,
                id=workflow_id,
                task_queue=task_queue,
            )

            logger.info(f"Temporal workflow triggered successfully: {workflow_id}")

            # Print to console as well
            print("\n" + "=" * 80)
            print("🎉 KAFKA EVENT RECEIVED & WORKFLOW TRIGGERED 🎉")
            print("=" * 80)
            print(f"Event: {body}")
            print(f"Workflow ID: {workflow_id}")
            print(f"Name: {name}")
            print("=" * 80 + "\n")

            # Return success response to Dapr
            return {"status": "SUCCESS", "workflow_id": workflow_id}

        except Exception as e:
            logger.error(f"Error processing Kafka event: {e}", exc_info=True)
            print(f"❌ Error processing Kafka event: {e}")
            import traceback

            traceback.print_exc()
            return {"status": "RETRY"}

    logger.info("Kafka listener endpoints registered successfully")


@observability(logger=logger, metrics=metrics, traces=traces)
async def main():
    logger.info("Starting hello world application with Kafka integration")
    # initialize application
    app = BaseApplication(name=APPLICATION_NAME)

    # setup workflow
    await app.setup_workflow(
        workflow_and_activities_classes=[(HelloWorldWorkflow, HelloWorldActivities)],
    )

    # start worker
    await app.start_worker()

    # Setup the application server
    await app.setup_server(workflow_class=HelloWorldWorkflow)

    # Register Kafka listener endpoints (must be after setup_server to get app.server.app)
    register_kafka_listener(app)

    # start server
    await app.start_server()


if __name__ == "__main__":
    asyncio.run(main())
