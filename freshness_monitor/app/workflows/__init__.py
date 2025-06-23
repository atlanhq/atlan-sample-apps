from datetime import timedelta  
from typing import Dict, Any, Sequence, Callable
from temporalio import workflow, activity
from temporalio.common import RetryPolicy  
from application_sdk.workflows import WorkflowInterface
from app.activities import FreshnessMonitorActivities
from application_sdk.activities import ActivitiesInterface


@workflow.defn  
class FreshnessMonitorWorkflow(WorkflowInterface):          
    @workflow.run  
    async def run(self, workflow_args: Dict[str, Any]) -> Dict[str, Any]:  
        """Main workflow execution"""  
        
        activities_instance = FreshnessMonitorActivities()
        
        workflow_args = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_args,
            start_to_close_timeout=timedelta(seconds=10),
        )
          
        # Extract configuration from workflow args  
        threshold_days = workflow_args.get("threshold_days", 30)  

        # Step 1: Fetch all table metadata  
        tables_data = await workflow.execute_activity_method(  
            activities_instance.fetch_tables_metadata,  
            workflow_args,  
            start_to_close_timeout=timedelta(minutes=1),  
        )  
          
        # Step 2: Identify stale tables  
        stale_tables = await workflow.execute_activity_method(  
            activities_instance.identify_stale_tables,  
            {
                "tables_data": tables_data,
                "threshold_days": threshold_days
            },
            start_to_close_timeout=timedelta(minutes=1),  
        )  
          
        if stale_tables:  
            await workflow.execute_activity_method(  
                activities_instance.tag_stale_tables,  
                {"stale_tables": stale_tables},  
                start_to_close_timeout=timedelta(minutes=1),  
            )  
      
    @staticmethod  
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable]:  
        """Return list of activity methods for worker registration"""  
        return [  
            activities.get_workflow_args,
            activities.fetch_tables_metadata,  
            activities.identify_stale_tables,  
            activities.tag_stale_tables  
        ] 