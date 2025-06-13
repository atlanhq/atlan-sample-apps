import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Type, cast

from dapr import clients
from temporalio import activity, workflow

from application_sdk.activities import ActivitiesInterface
from application_sdk.application import BaseApplication
from application_sdk.clients.utils import get_workflow_client
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.outputs.eventstore import (
    ApplicationEventNames,
    Event,
    EventMetadata,
    EventStore,
    EventTypes,
    WorkflowStates,
)
from application_sdk.worker import Worker
from events.workflows import SampleWorkflow
from events.activities import SampleActivities

logger = get_logger(__name__)

async def start_worker():
    workflow_client = get_workflow_client(
        application_name=APPLICATION_NAME,
    )
    await workflow_client.load()

    activities = SampleActivities()

    worker = Worker(
        workflow_client=workflow_client,
        workflow_activities=SampleWorkflow.get_activities(activities),
        workflow_classes=[SampleWorkflow],
        passthrough_modules=["application_sdk", "os", "pandas"],
    )

    # Start the worker in a separate thread
    await worker.start(daemon=True)

async def application_subscriber():
    # Open the application manifest in the current directory
    application_manifest = json.load(
        open(os.path.join(os.path.dirname(__file__), "subscriber_manifest.json"))
    )

    # 2 Steps to setup event registration,
    # 1. Setup the event in the manifest, with event name, type and filters => This creates an event trigger
    # 2. Register the event subscription to a workflow => This binds the workflow to the event trigger

    # Initialize the application
    application = BaseApplication(
        name=APPLICATION_NAME,
        application_manifest=application_manifest,  # Optional, if the manifest has event registration, it will be bootstrapped
        
    )

    # Register the event subscription to a workflow
    application.register_event_subscription("AssetExtractionCompleted", SampleWorkflow)

    # Can also register the events to multiple workflows
    # application.register_event_subscription("ErrorEvent", SampleWorkflow)

    # Setup the workflow is needed to start the worker
    await application.setup_workflow(
        workflow_classes=[SampleWorkflow], activities_class=SampleActivities
    )
    await application.start_worker()

    await application.setup_server(
        workflow_class=SampleWorkflow,
        ui_enabled=False,
    )

    await asyncio.gather(application.start_server(), simulate_worklflow_end_event())


async def simulate_worklflow_end_event():
    await asyncio.sleep(15)

    # Simulates that a dependent workflow has ended
    event = Event(
        metadata=EventMetadata(
            workflow_type="AssetExtractionWorkflow",
            workflow_state=WorkflowStates.COMPLETED.value,
            workflow_id="123",
            workflow_run_id="456",
            application_name="AssetExtractionApplication",
            event_published_client_timestamp=int(datetime.now().timestamp()),
        ),
        event_type=EventTypes.APPLICATION_EVENT.value,
        event_name=ApplicationEventNames.WORKFLOW_END.value,
        data={},
    )
    with clients.DaprClient() as client:
        client.publish_event(
            pubsub_name=EventStore.EVENT_STORE_NAME,
            topic_name=event.get_topic_name(),
            data=json.dumps(event.model_dump(mode="json")),
            data_content_type="application/json",
        )


if __name__ == "__main__":
    asyncio.run(application_subscriber())
