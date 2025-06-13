
from datetime import timedelta
from typing import Any, Callable, Dict, List, Type, cast
from application_sdk.outputs.eventstore import Event

from temporalio import workflow

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from events.activities import SampleActivities

logger = get_logger(__name__)


# Workflow that will be triggered by an event
@workflow.defn
class SampleWorkflow(WorkflowInterface):
    activities_cls: Type[ActivitiesInterface] = SampleActivities

    @workflow.run
    async def run(self, workflow_config: dict[str, Any]):
        # Get the workflow configuration from the state store
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            self.activities_cls.get_workflow_args,
            workflow_config,  # Pass the whole config containing workflow_id
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        workflow_run_id = workflow.info().run_id
        workflow_args["workflow_run_id"] = workflow_run_id

        # When a workflow is triggered by an event, the event is passed in as a dictionary
        event = Event(**workflow_args["event"])

        # We can also check the event data to get the workflow name and id
        workflow_type = event.metadata.workflow_type
        workflow_id = event.metadata.workflow_id

        print("workflow_type", workflow_type)
        print("workflow_id", workflow_id)

        await workflow.execute_activity_method(
            self.activities_cls.activity_1,
            start_to_close_timeout=timedelta(seconds=10),
            heartbeat_timeout=timedelta(seconds=10),
        )
        await workflow.execute_activity_method(
            self.activities_cls.activity_2,
            start_to_close_timeout=timedelta(seconds=10),
            heartbeat_timeout=timedelta(seconds=10),
        )

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> List[Callable[..., Any]]:
        sample_activities = cast(SampleActivities, activities)

        return [
            sample_activities.activity_1,
            sample_activities.activity_2,
            sample_activities.get_workflow_args,
        ]

