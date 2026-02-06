"""
Connector Workflow - Temporal Workflow Definition

The workflow orchestrates the sequence of activities:
1. Get workflow configuration
2. Extract metadata from source
3. Transform to Atlan format
4. Write output files

Note: Preflight checks are handled by the handler before workflow starts.
Workflows are deterministic - they should only call activities, not do I/O directly.
"""

from typing import Any, Dict, Type

from app.activities import ConnectorActivities
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows.metadata_extraction import MetadataExtractionWorkflow
from temporalio import workflow
from temporalio.common import RetryPolicy

logger = get_logger(__name__)
workflow.logger = logger

# Retry configuration for activities
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF = 2


@workflow.defn
class ConnectorWorkflow(MetadataExtractionWorkflow):
    """
    Main workflow for metadata extraction.

    This workflow coordinates the extraction, transformation, and output
    of metadata from your source system to Atlan.
    """

    activities_cls: Type[ConnectorActivities] = ConnectorActivities
    application_name: str = APPLICATION_NAME

    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        Execute the metadata extraction workflow.

        Args:
            workflow_config: Configuration from the UI/API trigger.
        """
        logger.info("Starting connector workflow")

        try:
            retry_policy = RetryPolicy(
                maximum_attempts=RETRY_MAX_ATTEMPTS,
                backoff_coefficient=RETRY_BACKOFF,
            )
            activities = self.activities_cls()
            workflow_args: Dict[str, Any] = {}

            # =================================================================
            # STEP 1: Get Workflow Configuration
            # =================================================================
            logger.info("Step 1: Getting workflow configuration")
            workflow_args = await workflow.execute_activity_method(
                activities.get_workflow_args,
                args=[workflow_config],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
            )
            workflow_args["workflow_run_id"] = workflow.info().run_id

            # =================================================================
            # STEP 2: Extract Metadata
            # =================================================================
            logger.info("Step 2: Extracting metadata")
            extract_result = await workflow.execute_activity_method(
                activities.extract_metadata,
                args=[workflow_args],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
            )
            logger.info(f"Extraction complete: {extract_result}")

            # =================================================================
            # STEP 3: Transform Metadata
            # =================================================================
            logger.info("Step 3: Transforming metadata")
            transform_result = await workflow.execute_activity_method(
                activities.transform_metadata,
                args=[workflow_args],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
            )
            logger.info(f"Transformation complete: {transform_result}")

            # =================================================================
            # STEP 4: Write Output
            # =================================================================
            logger.info("Step 4: Writing output")
            write_result = await workflow.execute_activity_method(
                activities.write_output,
                args=[workflow_args],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
            )
            logger.info(f"Write complete: {write_result}")

            logger.info("Workflow completed successfully")

        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            raise

    @staticmethod
    def get_activities(activities: ConnectorActivities) -> list:
        """
        Return list of activities for worker registration.

        This method is required by the SDK for Temporal worker setup.
        """
        return [
            activities.get_workflow_args,
            activities.extract_metadata,
            activities.transform_metadata,
            activities.write_output,
        ]
