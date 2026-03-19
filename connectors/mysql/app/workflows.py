"""
This file contains the workflow definition for the SQL metadata extraction application.

Note:
- The run method is overriden from the base class for demostration purposes.

Lakehouse Load:
- After extraction and transformation, the workflow can load data into an
  Iceberg lakehouse via the MDLH service. This is enabled by setting:
    ENABLE_LAKEHOUSE_LOAD=true
    LH_LOAD_RAW_NAMESPACE / LH_LOAD_RAW_TABLE_NAME      (raw parquet)
    LH_LOAD_TRANSFORMED_NAMESPACE / LH_LOAD_TRANSFORMED_TABLE_NAME  (transformed jsonl)
  See application_sdk.constants for all configuration options.
"""

import asyncio
from datetime import timedelta
from typing import Any, Callable, Dict, List

from app.activities import SQLMetadataExtractionActivities
from application_sdk.constants import (
    ENABLE_LAKEHOUSE_LOAD,
    LH_LOAD_RAW_MODE,
    LH_LOAD_RAW_NAMESPACE,
    LH_LOAD_RAW_TABLE_NAME,
)
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.workflows.metadata_extraction.sql import (
    BaseSQLMetadataExtractionWorkflow,
)
from temporalio import workflow
from temporalio.common import RetryPolicy

logger = get_logger(__name__)
workflow.logger = logger
metrics = get_metrics()
traces = get_traces()


@workflow.defn
class SQLMetadataExtractionWorkflow(BaseSQLMetadataExtractionWorkflow):
    @observability(logger=logger, metrics=metrics, traces=traces)
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]):
        """
        Run the workflow.

        :param workflow_args: The workflow arguments.
        """
        activities_instance = SQLMetadataExtractionActivities()

        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        retry_policy = RetryPolicy(
            maximum_attempts=6,
            backoff_coefficient=2,
        )

        await workflow.execute_activity_method(
            activities_instance.preflight_check,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        await workflow.execute_activity_method(
            activities_instance.credential_extraction_demo_activity,
            workflow_args,
            retry_policy=retry_policy,
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        fetch_and_transforms = [
            self.fetch_and_transform(
                activities_instance.fetch_databases,
                workflow_args,
                retry_policy,
            ),
            self.fetch_and_transform(
                activities_instance.fetch_schemas,
                workflow_args,
                retry_policy,
            ),
            self.fetch_and_transform(
                activities_instance.fetch_tables,
                workflow_args,
                retry_policy,
            ),
            self.fetch_and_transform(
                activities_instance.fetch_columns,
                workflow_args,
                retry_policy,
            ),
        ]
        await asyncio.gather(*fetch_and_transforms)

        # --- Lakehouse Load (raw) ---
        # After all fetches complete, load raw parquet files into an Iceberg table.
        # Enabled via ENABLE_LAKEHOUSE_LOAD=true + LH_LOAD_RAW_NAMESPACE/TABLE_NAME env vars.
        if (
            ENABLE_LAKEHOUSE_LOAD
            and LH_LOAD_RAW_NAMESPACE
            and LH_LOAD_RAW_TABLE_NAME
        ):
            await self._execute_lakehouse_load(
                workflow_args,
                output_path=f"{workflow_args.get('output_path', '')}/raw",
                namespace=LH_LOAD_RAW_NAMESPACE,
                table_name=LH_LOAD_RAW_TABLE_NAME,
                mode=LH_LOAD_RAW_MODE,
                file_extension=".parquet",
            )

        # --- Exit activities (upload to Atlan + lakehouse load for transformed) ---
        # run_exit_activities handles:
        #   1. upload_to_atlan (if ENABLE_ATLAN_UPLOAD=true)
        #   2. load_to_lakehouse for transformed jsonl (if ENABLE_LAKEHOUSE_LOAD=true
        #      + LH_LOAD_TRANSFORMED_NAMESPACE/TABLE_NAME env vars)
        await self.run_exit_activities(workflow_args)

    @staticmethod
    def get_activities(
        activities: SQLMetadataExtractionActivities,
    ) -> List[Callable[..., Any]]:
        """Get the list of activities for the workflow.

        Args:
            activities: The activities instance containing the workflow activities.

        Returns:
            List[Callable[..., Any]]: A list of activity methods that can be executed by the workflow.
        """
        return [
            activities.get_workflow_args,
            activities.preflight_check,
            activities.fetch_databases,
            activities.fetch_schemas,
            activities.fetch_tables,
            activities.fetch_columns,
            activities.credential_extraction_demo_activity,
            activities.transform_data,
            activities.upload_to_atlan,
            activities.load_to_lakehouse,
        ]
