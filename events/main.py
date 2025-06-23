import asyncio
import json
import os

from application_sdk.application import BaseApplication
from application_sdk.clients.utils import get_workflow_client
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.worker import Worker
from events.workflows import WorkflowTriggeredByEvent, WorkflowTriggeredByUI
from events.activities import SampleActivities

logger = get_logger(__name__)

APPLICATION_NAME = "events-app"

async def start_worker():
    workflow_client = get_workflow_client(
        application_name=APPLICATION_NAME,
    )
    await workflow_client.load()

    activities = SampleActivities()

    worker = Worker(
        workflow_client=workflow_client,
        workflow_activities=WorkflowTriggeredByEvent.get_activities(activities),
        workflow_classes=[WorkflowTriggeredByEvent],
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
    application.register_event_subscription("WorkflowTriggeredByUICompleted", WorkflowTriggeredByEvent)

    # Can also register the events to multiple workflows
    # application.register_event_subscription("ErrorEvent", WorkflowTriggeredByEvent)

    # Setup the workflow is needed to start the worker
    await application.setup_workflow(
        workflow_classes=[WorkflowTriggeredByEvent, WorkflowTriggeredByUI], activities_class=SampleActivities
    )
    await application.start_worker()

    await application.setup_server(
        workflow_class=WorkflowTriggeredByUI,
    )

    await application.start_server()

if __name__ == "__main__":
    asyncio.run(application_subscriber())
