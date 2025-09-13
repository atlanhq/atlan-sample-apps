from typing import Any, Dict, Type

from app.activities import AppMetadataExtractionActivities
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows.metadata_extraction import MetadataExtractionWorkflow
from temporalio import workflow
from temporalio.common import RetryPolicy

# Constants for activity retry policies
ACTIVITY_RETRY_MAX_ATTEMPTS = 3
ACTIVITY_RETRY_BACKOFF_COEFFICIENT = 2

logger = get_logger(__name__)
workflow.logger = logger


@workflow.defn
class AppMetadataExtractionWorkflow(MetadataExtractionWorkflow):
    """App metadata extraction workflow orchestrator"""

    activities_cls: Type[AppMetadataExtractionActivities] = (
        AppMetadataExtractionActivities
    )
    application_name: str = APPLICATION_NAME

    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """Simplified App metadata extraction workflow."""

        logger.info("Starting App metadata extraction workflow")

        try:
            workflow_run_id = workflow.info().run_id
            workflow_args: Dict[str, Any] = {}  # Initialize workflow_args

            # activity retry policy
            retry_policy = RetryPolicy(
                maximum_attempts=ACTIVITY_RETRY_MAX_ATTEMPTS,
                backoff_coefficient=ACTIVITY_RETRY_BACKOFF_COEFFICIENT,
            )

            # Execute setup activities first
            activities_instance = self.activities_cls()

            # STEP 1: Get workflow configuration
            logger.info("Executing get_workflow_args")
            result = await workflow.execute_activity_method(
                activities_instance.get_workflow_args,
                args=[workflow_config],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
                summary="Get workflow args",
            )
            workflow_args = result
            workflow_args["workflow_run_id"] = workflow_run_id

            # STEP 2: Preflight checks
            logger.info("Executing preflight_check")
            await workflow.execute_activity_method(
                activities_instance.preflight_check,
                args=[workflow_args],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
                summary="Preflight check",
            )

            # STEP 3: Set metadata filter state variables
            # NOTE: This activity is used to evaluate the precedence of the metadata filters and to maintain
            # state variables, which can be used in subsequent acitivities without needing to evaluate the filter precedence again
            logger.info("Executing set_metadata_filter_state")
            await workflow.execute_activity_method(
                activities_instance.set_metadata_filter_state,
                args=[workflow_args],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
                summary="Set metadata filter state",
            )

            # STEP 4: Extract apps
            logger.info("Extracting Apps")
            app_statistics = await workflow.execute_activity_method(
                activities_instance.extract_apps,
                args=[workflow_args],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
                summary="Extract Apps",
            )
            logger.info(f"App extraction completed: {app_statistics}")

            # STEP 5: Extract pages
            logger.info("Extracting Pages")
            page_statistics = await workflow.execute_activity_method(
                activities_instance.extract_pages,
                args=[workflow_args],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
                summary="Extract Pages",
            )
            logger.info(f"Page extraction completed: {page_statistics}")

            # STEP 6: Transform extracted data
            asset_types = ["app", "page"]
            for asset_type in asset_types:
                logger.info(f"Transforming {asset_type}")
                workflow_args["typename"] = asset_type
                
                await workflow.execute_activity_method(
                    activities_instance.transform_data,
                    args=[workflow_args],
                    retry_policy=retry_policy,
                    start_to_close_timeout=self.default_start_to_close_timeout,
                    heartbeat_timeout=self.default_heartbeat_timeout,
                    summary=f"Transform {asset_type}",
                )
                logger.info(f"Successfully transformed {asset_type}")

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_activities(
        activities: AppMetadataExtractionActivities,
    ) -> list:
        """Register the activities to be executed by the workflow.

        ------------------------------------------------------------
        NOTE: This is a necessary function for worker registration, thus exists here. Not used for execution order, as executioin is controlled in the run method.
        """
        return [
            activities.get_workflow_args,  # NOTE: Present in ActicityInterface
            activities.preflight_check,  # NOTE: Present in ActicityInterface
            activities.set_metadata_filter_state,
            activities.extract_apps,
            activities.extract_pages,
            activities.transform_data,
        ]

