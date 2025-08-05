from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import AssetDescriptionReminderActivities
from application_sdk.activities import ActivitiesInterface
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

        workflow.logger.info(f"Retrieved full workflow args: {workflow_args}")

        # Step 1: Fetch assets owned by the selected user (up to the specified limit)
        assets_data = await workflow.execute_activity_method(
            activities_instance.fetch_user_assets,
            workflow_args,
            start_to_close_timeout=timedelta(minutes=1),
        )

        # Step 2: Check if description of any asset is empty, get the first one
        asset_without_description = await workflow.execute_activity_method(
            activities_instance.find_asset_without_description,
            {"assets_data": assets_data},
            start_to_close_timeout=timedelta(minutes=1),
        )

        if not asset_without_description or not asset_without_description.get("assets"):
            workflow.logger.info("No assets without description found")
            return {"success": True, "message": "No assets without description found"}

        # Step 3: Find the person by name in Slack
        slack_user = await workflow.execute_activity_method(
            activities_instance.find_slack_user,
            workflow_args,
            start_to_close_timeout=timedelta(minutes=1),
        )

        # Step 4: Send Slack message to the person about missing description
        await workflow.execute_activity_method(
            activities_instance.send_slack_reminder,
            {
                "slack_user": slack_user,
                "assets": asset_without_description["assets"],
                "user_username": workflow_args["user_username"],
                "config": workflow_args["config"],
            },
            start_to_close_timeout=timedelta(minutes=1),
        )

        return {
            "success": True,
            "message": f"Found {asset_without_description['count']} assets without description and sent reminder",
            "assets_count": asset_without_description["count"],
        }

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable]:
        """Return list of activity methods for worker registration"""
        return [
            activities.get_workflow_args,
            activities.fetch_user_assets,
            activities.find_asset_without_description,
            activities.find_slack_user,
            activities.send_slack_reminder,
        ]
