from datetime import timedelta  
from typing import Dict, Any, Sequence, Callable
from temporalio import workflow, activity
from temporalio.common import RetryPolicy  
  
@workflow.defn  
class AssetDescriptionReminderWorkflow:          
    @workflow.run  
    async def run(self, initial_args: Dict[str, Any]) -> Dict[str, Any]:  
        """Main workflow execution for asset description reminder"""  
        
        workflow.logger.info(f"Workflow started with initial args: {initial_args}")
        
        # Define retry policy for activities  
        retry_policy = RetryPolicy(  
            initial_interval=timedelta(seconds=1),  
            maximum_interval=timedelta(seconds=10),  
            maximum_attempts=3  
        )

        # Get the full workflow arguments from the state store
        workflow_args: Dict[str, Any] = await workflow.execute_activity(
            "get_workflow_args",
            initial_args,
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"Retrieved full workflow args: {workflow_args}")
          
        # Extract user information from workflow args  
        user_username = workflow_args.get("user_username")
        user_id = workflow_args.get("user_id")
        
        if not user_username:
            return {"error": "user_username is required"}
          
        # Step 1: Fetch 50 most assets owned by the selected user
        assets_data = await workflow.execute_activity(  
            "fetch_user_assets",  
            {"user_username": user_username, "limit": 50},
            start_to_close_timeout=timedelta(minutes=5),  
            retry_policy=retry_policy  
        )  
          
        if not assets_data:
            return {
                "user_username": user_username,
                "assets_checked": 0,
                "asset_without_description": None,
                "slack_message_sent": False,
                "message": "No assets found for this user"
            }
        
        # Step 2: Check if description of any asset is empty, get the first one  
        asset_without_description = await workflow.execute_activity(  
            "find_asset_without_description",  
            {"assets_data": assets_data},
            start_to_close_timeout=timedelta(minutes=2),  
            retry_policy=retry_policy  
        )
          
        if not asset_without_description:
            return {
                "user_username": user_username,
                "assets_checked": len(assets_data),
                "asset_without_description": None,
                "slack_message_sent": False,
                "message": "All assets have descriptions"
            }
        
        # Step 3: Find the person by name in Slack
        slack_user = await workflow.execute_activity(  
            "find_slack_user",  
            {"username": user_username},
            start_to_close_timeout=timedelta(minutes=2),  
            retry_policy=retry_policy  
        )  
        
        if not slack_user:
            return {
                "user_username": user_username,
                "assets_checked": len(assets_data),
                "asset_without_description": asset_without_description,
                "slack_message_sent": False,
                "message": f"User {user_username} not found in Slack"
            }
        
        # Step 4: Send Slack message to the person about missing description
        slack_result = await workflow.execute_activity(  
            "send_slack_reminder",  
            {
                "slack_user": slack_user,
                "asset": asset_without_description,
                "user_username": user_username
            },
            start_to_close_timeout=timedelta(minutes=2),  
            retry_policy=retry_policy  
        )  
          
        # Return summary  
        return {  
            "user_username": user_username,
            "assets_checked": len(assets_data),
            "asset_without_description": asset_without_description,
            "slack_user_found": slack_user,
            "slack_message_sent": slack_result.get("success", False),
            "slack_message_id": slack_result.get("message_id"),
            "message": "Reminder sent successfully" if slack_result.get("success") else "Failed to send reminder"
        }  
      
    @staticmethod  
    def get_activities(activities_instance) -> Sequence[Callable]:  
        """Return list of activity methods for worker registration"""  
        return [  
            activities_instance.get_workflow_args,
            activities_instance.fetch_user_assets,  
            activities_instance.find_asset_without_description,  
            activities_instance.find_slack_user,
            activities_instance.send_slack_reminder
        ] 