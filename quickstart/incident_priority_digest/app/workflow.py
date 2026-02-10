from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import IncidentDigestActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow
from temporalio.common import RetryPolicy

logger = get_logger(__name__)
workflow.logger = logger


@workflow.defn
class IncidentDigestWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """Orchestrate the incident priority digest.

        1. Retrieve workflow args (includes ``records_json``).
        2. Parse incident records.
        3. Write raw output.
        4. Generate digest and write transformed output.
        """
        activities = IncidentDigestActivities()

        retry_policy = RetryPolicy(
            maximum_attempts=6,
            backoff_coefficient=2,
        )

        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities.get_workflow_args,
            workflow_config,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(seconds=10),
        )

        records = await workflow.execute_activity_method(
            activities.parse_records,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(seconds=30),
        )

        output_path = workflow_args.get("output_path", "./local/tmp/output")

        await workflow.execute_activity_method(
            activities.write_raw_output,
            {"output_path": output_path, "records": records},
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(seconds=30),
        )

        await workflow.execute_activity_method(
            activities.generate_and_write_digest,
            {"output_path": output_path, "records": records},
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(seconds=30),
        )

        logger.info("Incident digest workflow completed")

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        if not isinstance(activities, IncidentDigestActivities):
            raise TypeError(
                "Activities must be an instance of IncidentDigestActivities"
            )

        return [
            activities.get_workflow_args,
            activities.parse_records,
            activities.write_raw_output,
            activities.generate_and_write_digest,
        ]
