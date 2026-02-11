"""
Workflow definition for Starburst Enterprise (SEP) metadata extraction.

Orchestrates a hybrid extraction pipeline:
1. Fetch workflow args + preflight check
2. Parallel execution of:
   - REST stream: Domains, Data Products, Datasets + Dataset Columns
   - SQL stream: Catalogs, Schemas, Tables, Columns
3. (Future) Join/merge step to correlate Data Products with SQL schemas
"""

import asyncio
from datetime import timedelta
from typing import Any, Callable, Dict, List

from app.activities import SEPMetadataExtractionActivities
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow
from temporalio.common import RetryPolicy

logger = get_logger(__name__)
workflow.logger = logger
metrics = get_metrics()
traces = get_traces()


@workflow.defn
class SEPMetadataExtractionWorkflow(WorkflowInterface):
    """Temporal workflow for Starburst Enterprise metadata extraction.

    Execution order:
    1. get_workflow_args - Retrieve configuration from state store
    2. preflight_check - Validate REST + SQL connectivity
    3. Parallel fan-out:
       a. REST stream: fetch_domains, fetch_data_products, extract_datasets_from_products
       b. SQL stream: fetch_catalogs, fetch_schemas, fetch_tables, fetch_columns
    """

    default_start_to_close_timeout = timedelta(hours=2)
    default_heartbeat_timeout = timedelta(minutes=2)

    @observability(logger=logger, metrics=metrics, traces=traces)
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        activities = SEPMetadataExtractionActivities()

        retry_policy = RetryPolicy(
            maximum_attempts=6,
            backoff_coefficient=2,
        )

        # Step 1: Retrieve full workflow args from state store
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Step 2: Preflight check - validate both REST and SQL connectivity
        await workflow.execute_activity_method(
            activities.preflight_check,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        # Step 3: Parallel extraction - REST and SQL streams run concurrently
        rest_stream = self._run_rest_extraction(activities, workflow_args, retry_policy)
        sql_stream = self._run_sql_extraction(activities, workflow_args, retry_policy)

        await asyncio.gather(rest_stream, sql_stream)

        logger.info("SEP metadata extraction workflow completed successfully")

    async def _run_rest_extraction(
        self,
        activities: SEPMetadataExtractionActivities,
        workflow_args: Dict[str, Any],
        retry_policy: RetryPolicy,
    ) -> None:
        """REST extraction stream: Domains, Data Products, Datasets."""
        # Fetch domains
        await workflow.execute_activity_method(
            activities.fetch_domains,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        # Fetch data products (contains embedded datasets)
        await workflow.execute_activity_method(
            activities.fetch_data_products,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        # Extract datasets and columns from data product responses
        await workflow.execute_activity_method(
            activities.extract_datasets_from_products,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

    async def _run_sql_extraction(
        self,
        activities: SEPMetadataExtractionActivities,
        workflow_args: Dict[str, Any],
        retry_policy: RetryPolicy,
    ) -> None:
        """SQL extraction stream: Catalogs, Schemas, Tables, Columns."""
        # Fetch catalogs first (needed by downstream activities)
        await workflow.execute_activity_method(
            activities.fetch_catalogs,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        # Fetch schemas, tables, and columns in parallel
        await asyncio.gather(
            workflow.execute_activity_method(
                activities.fetch_schemas,
                workflow_args,
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
            ),
            workflow.execute_activity_method(
                activities.fetch_tables,
                workflow_args,
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
            ),
            workflow.execute_activity_method(
                activities.fetch_columns,
                workflow_args,
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
            ),
        )

    @staticmethod
    def get_activities(
        activities: SEPMetadataExtractionActivities,
    ) -> List[Callable[..., Any]]:
        """Register all activities with the Temporal worker."""
        return [
            # Base activities from SDK
            activities.get_workflow_args,
            activities.preflight_check,
            # REST activities
            activities.fetch_domains,
            activities.fetch_data_products,
            activities.extract_datasets_from_products,
            # SQL activities
            activities.fetch_catalogs,
            activities.fetch_schemas,
            activities.fetch_tables,
            activities.fetch_columns,
        ]
