import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Sequence, Type

from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows.metadata_extraction.sql import (
    BaseSQLMetadataExtractionWorkflow,
)
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.workflow import ParentClosePolicy

from app.activities.metadata_extraction.redshift import (
    RedshiftSQLMetadataExtractionActivities,
)

logger = get_logger(__name__)


@workflow.defn
class RedshiftMetadataExtractionWorkflow(BaseSQLMetadataExtractionWorkflow):
    """
    Workflow for extracting metadata from Redshift
    """

    activities_cls: Type[RedshiftSQLMetadataExtractionActivities] = (  # type: ignore
        RedshiftSQLMetadataExtractionActivities
    )

    @staticmethod
    def get_activities(  # type: ignore
        activities: RedshiftSQLMetadataExtractionActivities,
    ) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (ActivitiesInterface): The activities instance
                containing the metadata extraction operations.

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods to be executed
                in order, including preflight check, fetching databases, schemas,
                tables, columns, and transforming data.
        """
        return [
            activities.preflight_check,
            activities.get_workflow_args,
            activities.fetch_databases,
            activities.fetch_schemas,
            activities.fetch_tables,
            activities.fetch_columns,
            activities.fetch_procedures,
            activities.transform_data,
            activities.upload_to_atlan,
            activities.save_workflow_state,
        ]

    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]):
        """
        Run the workflow.

        :param workflow_config: The workflow arguments.
        """
        workflow_id = workflow_config["workflow_id"]
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            self.activities_cls.get_workflow_args,
            workflow_config,  # Pass the whole config containing workflow_id
            retry_policy=RetryPolicy(maximum_attempts=3, backoff_coefficient=2),
            start_to_close_timeout=self.default_start_to_close_timeout,
            heartbeat_timeout=self.default_heartbeat_timeout,
        )

        if str(os.getenv("ATLAN_ENABLE_REDSHIFT_EXTRACTION", "true")).lower() == "true":
            await super().run(workflow_config)

        if str(os.getenv("ATLAN_ENABLE_REDSHIFT_MINER", "true")).lower() == "true":
            await self.run_miner(workflow_args, workflow_id)

        # Run the exit activities
        await self.run_exit_activities(workflow_args)

    async def run_miner(self, workflow_args: Dict[str, Any], workflow_id: str):
        if workflow_args.get("miner_args"):
            miner_workflow_config = {
                "chunk_size": 6000,
                "timestamp_column": "starttime",
                "sql_replace_from": "CAST(EXTRACT(epoch from starttime) as INT8) * 1000 > [START_MARKER]",
                "sql_replace_to": "CAST(EXTRACT(epoch from starttime) as INT8) * 1000 > [START_MARKER] and CAST(EXTRACT(epoch from starttime) as INT8) * 1000 < [END_MARKER]",
                "ranged_sql_start_key": "[START_MARKER]",
                "ranged_sql_end_key": "[END_MARKER]",
            }
            workflow_args["miner_args"].update(miner_workflow_config)

            # Use activity to save state instead of calling StateStore directly
            await workflow.execute_activity_method(
                self.activities_cls.save_workflow_state,
                args=[workflow_id, workflow_args],
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    backoff_coefficient=2,
                ),
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
            )

            # Trigger miner workflow
            await workflow.execute_child_workflow(
                "RedshiftQueryExtractionWorkflow",
                workflow_args,
                id=f"redshift-miner-{workflow_id}",
                parent_close_policy=ParentClosePolicy.ABANDON,
            )

            logger.info(f"Extraction workflow completed for {workflow_id}")

    @staticmethod
    async def get_configmap(config_map_id: str) -> Dict[str, Any]:
        workflow_json_path = Path().cwd() / "app" / "templates" / "workflow.json"
        credential_json_path = (
            Path().cwd() / "app" / "templates" / "atlan-connectors-redshift.json"
        )

        if config_map_id == "atlan-connectors-redshift":
            with open(credential_json_path) as f:
                return json.load(f)

        with open(workflow_json_path) as f:
            return json.load(f)
