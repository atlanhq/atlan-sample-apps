from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import (
    FetchTablesMetadataInput,
    FreshnessMonitorActivities,
    TagStaleTablesOutput,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

logger = get_logger(__name__)


@dataclass
class Total:
    tables_read: int = 0
    stale_tables: int = 0
    failed_count: int = 0
    tagged_count: int = 0

    def add_tagged_counts(self, tagged_counts: TagStaleTablesOutput) -> None:
        self.tagged_count += tagged_counts.tagged_count
        self.failed_count += tagged_counts.failed_count


@workflow.defn
class FreshnessMonitorWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_args: Dict[str, Any]):
        """Main workflow execution"""
        total = Total()
        logger.info("-" * 80)
        logger.info(f"Starting workflow {total}")
        logger.info(f"Total tables_read: {total.tables_read}")
        logger.info(f"Total stale_tables: {total.stale_tables}")
        logger.info(f"Total tagged_count: {total.tagged_count}")
        logger.info(f"Total failed_count: {total.failed_count}")
        logger.info("-" * 80)
        activities_instance = FreshnessMonitorActivities()

        workflow_args = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_args,
            start_to_close_timeout=timedelta(seconds=60),
        )

        # Extract configuration from workflow args
        threshold_days = workflow_args.get("threshold_days", 30)
        start = 0
        metadata_input = FetchTablesMetadataInput(start=start, page_size=300)
        while True:
            # Step 1: Fetch a page of table metadata
            tables_data = await workflow.execute_activity_method(
                activities_instance.fetch_tables_metadata,
                metadata_input,
                start_to_close_timeout=timedelta(minutes=5),
            )
            # Step 2: If not more data available exit loop
            if not tables_data:
                break
            total.tables_read += len(tables_data)
            # Step 3: Identify stale tables
            stale_tables = await workflow.execute_activity_method(
                activities_instance.identify_stale_tables,
                {"tables_data": tables_data, "threshold_days": threshold_days},
                start_to_close_timeout=timedelta(minutes=5),
            )

            # Step 4: Tag stale tables
            if stale_tables:
                tag_output = await workflow.execute_activity_method(
                    activities_instance.tag_stale_tables,
                    {"stale_tables": stale_tables},
                    start_to_close_timeout=timedelta(minutes=60),
                )
                total.add_tagged_counts(tag_output)

            metadata_input.increment_start()
        logger.info(f"Total tables_read: {total.tables_read}")
        logger.info(f"Total stale_tables: {total.stale_tables}")
        logger.info(f"Total tagged_count: {total.tagged_count}")
        logger.info(f"Total failed_count: {total.failed_count}")

    @staticmethod
    def get_activities(activities: FreshnessMonitorActivities) -> Sequence[Callable]:
        """Return list of activity methods for worker registration"""
        return [
            activities.get_workflow_args,
            activities.fetch_tables_metadata,
            activities.identify_stale_tables,
            activities.tag_stale_tables,
        ]
