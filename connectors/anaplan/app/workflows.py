from typing import Any, Dict, Type

from application_sdk.activities.common.models import ActivityStatistics
from application_sdk.constants import APPLICATION_NAME
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows.metadata_extraction import MetadataExtractionWorkflow
from temporalio import workflow
from temporalio.common import RetryPolicy

from app.activities import AnaplanMetadataExtractionActivities

logger = get_logger(__name__)
workflow.logger = logger


@workflow.defn
class AnaplanMetadataExtractionWorkflow(MetadataExtractionWorkflow):
    """Anaplan metadata extraction workflow orchestrator"""

    activities_cls: Type[AnaplanMetadataExtractionActivities] = (
        AnaplanMetadataExtractionActivities
    )
    application_name: str = APPLICATION_NAME

    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """Main workflow execution method with activity orchestration.

        ------------------------------------------------------------
        INPUTS: workflow_config dict from frontend (workflow_id)

        WORKFLOW_CONFIG STRUCTURE:
        {
            "workflow_id": "<workflow_id>"
        }
        """
        logger.info("Starting Anaplan metadata extraction workflow")
        logger.info(f"Workflow config received: {workflow_config}")

        logger.info("Starting workflow execution")

        try:
            workflow_run_id = workflow.info().run_id
            workflow_args: Dict[str, Any] = {}  # Initialize workflow_args

            # activity retry policy
            retry_policy = RetryPolicy(maximum_attempts=2, backoff_coefficient=2)

            # Execute setup activities first
            activities_instance = self.activities_cls()

            # STEP 1: Get workflow configuration
            logger.info("Executing get_workflow_args")
            result = await workflow.execute_activity_method(
                activities_instance.get_workflow_args,
                args=[workflow_config],
                retry_policy=RetryPolicy(maximum_attempts=3, backoff_coefficient=2),
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

            # STEP 3: Set metadata filter state
            logger.info("Executing set_metadata_filter_state")
            await workflow.execute_activity_method(
                activities_instance.set_metadata_filter_state,
                args=[workflow_args],
                retry_policy=retry_policy,
                start_to_close_timeout=self.default_start_to_close_timeout,
                heartbeat_timeout=self.default_heartbeat_timeout,
                summary="Set metadata filter state",
            )

            # STEP 4: Extract all asset types sequentially
            extracted_asset_types = []
            asset_extraction_activities = self.get_asset_extraction_activities()

            for activity_method_name in asset_extraction_activities:
                asset_type = self.get_asset_type_from_activity(activity_method_name)
                logger.info(f"Extracting asset type: {asset_type}")

                try:
                    # Get the actual activity method from the activities instance
                    activity_method = getattr(
                        activities_instance, activity_method_name, None
                    )
                    if not activity_method:
                        logger.warning(
                            f"Activity method not found: {activity_method_name}"
                        )
                        continue

                    extraction_statistics = await workflow.execute_activity_method(
                        activity_method,
                        args=[workflow_args],
                        retry_policy=retry_policy,
                        start_to_close_timeout=self.default_start_to_close_timeout,
                        heartbeat_timeout=self.default_heartbeat_timeout,
                        summary=f"Extract {asset_type}",
                    )

                    # Check if extraction was successful and has data
                    logger.info(
                        f"Extraction statistics for {asset_type}: {extraction_statistics}"
                    )
                    if extraction_statistics and self.is_asset_extracted(
                        extraction_statistics
                    ):
                        extracted_asset_types.append(asset_type)
                        record_count = extraction_statistics.total_record_count

                        logger.info(
                            f"Successfully extracted {asset_type} with {record_count} records"
                        )
                    else:
                        logger.warning(
                            f"No data extracted for {asset_type}. Statistics: {extraction_statistics}"
                        )

                except Exception as e:
                    logger.error(f"Failed to extract {asset_type}: {str(e)}")
                    # Continue with other assets even if one fails

            # Store extracted asset types in workflow args
            workflow_args["extracted_asset_types"] = extracted_asset_types
            logger.info(
                f"Extraction completed. Extracted assets: {extracted_asset_types}"
            )

            # STEP 5: Transform each extracted asset type
            for asset_type in extracted_asset_types:
                logger.info(f"Transforming asset type: {asset_type}")

                # Set typename for transformation
                transform_workflow_args = workflow_args.copy()
                transform_workflow_args["typename"] = asset_type

                try:
                    await workflow.execute_activity_method(
                        activities_instance.transform_data,
                        args=[transform_workflow_args],
                        retry_policy=retry_policy,
                        start_to_close_timeout=self.default_start_to_close_timeout,
                        heartbeat_timeout=self.default_heartbeat_timeout,
                        summary=f"Transform {asset_type}",
                    )
                    logger.info(f"Successfully transformed {asset_type}")
                except Exception as e:
                    logger.error(f"Failed to transform {asset_type}: {str(e)}")
                    raise e

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_activities(
        activities: AnaplanMetadataExtractionActivities,
    ) -> list:
        """Register the activities to be executed by the workflow.

        ------------------------------------------------------------
        NOTE: This is a necessary function for worker registration, thus exists here. Not used for execution order, as executioin is controlled in the run method.
        """
        return [
            activities.get_workflow_args, # NOTE: Present in ActicityInterface
            activities.preflight_check, # NOTE: Present in ActicityInterface
            activities.set_metadata_filter_state,
            activities.extract_anaplanapp,
            activities.extract_anaplanpage,
            activities.transform_data,
        ]

    @staticmethod
    def get_asset_extraction_activities() -> list:
        """Get the sequence of asset extraction activities.

        ------------------------------------------------------------
        OUTPUTS: List of asset extraction activity method names.
        """
        return [
            "extract_anaplanapp",
            "extract_anaplanpage",
        ]

    @staticmethod
    def get_asset_type_from_activity(activity_name: str) -> str:
        """Extract asset type from activity method name.

        ------------------------------------------------------------
        INPUTS: activity_name (str) - e.g., "extract_anaplanapp"
        OUTPUTS: asset_type (str) - e.g., "anaplanapp"
        """
        # Remove "extract_" prefix
        asset_type = activity_name.replace("extract_", "")
        return asset_type

    @staticmethod
    def is_asset_extracted(extraction_statistics: ActivityStatistics) -> bool:
        """Check if asset was successfully extracted based on statistics.

        ------------------------------------------------------------
        INPUTS: extraction_statistics (ActivityStatistics) - Pydantic model from extraction activity
        OUTPUTS: bool - True if asset has data, False otherwise
        """
        if not extraction_statistics:
            return False

        chunk_count = extraction_statistics.chunk_count
        total_record_count = extraction_statistics.total_record_count

        return chunk_count > 0 and total_record_count > 0
