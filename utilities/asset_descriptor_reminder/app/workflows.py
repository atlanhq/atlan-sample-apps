from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import AssetDescriptionReminderActivities
from app.models import FetchUserAssetsInput, SendSlackReminderInput, UploadDataInput
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow


@workflow.defn
class AssetDescriptionReminderWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, initial_args: Dict[str, Any]) -> Dict[str, Any]:
        """Main workflow execution for asset description reminder"""

        workflow.logger.info(f"Workflow started with initial args: {initial_args}")

        activities_instance = AssetDescriptionReminderActivities()

        # Get the full workflow arguments from the state store with configuration
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            initial_args,
            start_to_close_timeout=timedelta(minutes=1),
        )
        fetch_user_assets_input = FetchUserAssetsInput(
            config=workflow_args["config"],
            user_username=workflow_args["user_username"],
            asset_limit=workflow_args["asset_limit"],
        )
        count_of_assets_without_descriptions = 0
        # Since retrieving and processing all the assets at one time could take some time, we want
        # break the process down into smaller steps. We will retrieve and process one page of assets
        # at a time. Once all assets have been processed, if we have assets that are missing descriptions,
        # we will send a message to slack and upload the assets as a file.
        while True:
            # Step 1: Fetch 1 page of assets owned by the selected user
            assets_data = await workflow.execute_activity_method(
                activities_instance.fetch_user_assets,
                fetch_user_assets_input,
                start_to_close_timeout=timedelta(minutes=1),
            )
            # When no more assets are found exit the while loop
            if not assets_data:
                break
            # Step 2: Check if description of any asset is empty
            assets_without_descriptions = await workflow.execute_activity_method(
                activities_instance.find_asset_without_description,
                assets_data,
                start_to_close_timeout=timedelta(minutes=1),
            )
            if assets_without_descriptions:
                count_of_assets_without_descriptions += len(assets_without_descriptions)
                upload_data = UploadDataInput(
                    assets_data=assets_without_descriptions,
                    offset=fetch_user_assets_input.start,
                )
                # Step 3: Upload the assets without a description to object store
                # Since each activity could theoretically run on a different machine, we need
                # to save each set of data to the object store. We do this by saving the assets
                # locally to a json file, and uploading the file to object storage.
                await workflow.execute_activity_method(
                    activities_instance.upload_data,
                    upload_data,
                    start_to_close_timeout=timedelta(minutes=1),
                )
            # Increment start to retrieve the new page of assets
            fetch_user_assets_input.increment_start()
        workflow.logger.info(
            f"Assets without descriptions: {count_of_assets_without_descriptions}"
        )

        if count_of_assets_without_descriptions:
            # Step 4: Send Slack message to the person about missing description
            # Now that all the data has been processed, we will download all this files
            # from object storage, concatenate them in one file and upload that file to slack
            # along with an appropriate message.
            await workflow.execute_activity_method(
                activities_instance.send_slack_reminder,
                SendSlackReminderInput(
                    config=workflow_args["config"],
                    count_of_assets_without_description=count_of_assets_without_descriptions,
                ),
                start_to_close_timeout=timedelta(minutes=1),
            )
            # Step 5: Purge intermediate files from object storage
            (
                await workflow.execute_activity_method(
                    activities_instance.purge_files,
                    start_to_close_timeout=timedelta(minutes=1),
                ),
            )
        else:
            workflow.logger.info("No assets without descriptions")

    @staticmethod
    def get_activities(
        activities: AssetDescriptionReminderActivities,
    ) -> Sequence[Callable]:
        """Return list of activity methods for worker registration"""
        return [
            activities.get_workflow_args,
            activities.fetch_user_assets,
            activities.find_asset_without_description,
            activities.purge_files,
            activities.upload_data,
            activities.send_slack_reminder,
        ]
