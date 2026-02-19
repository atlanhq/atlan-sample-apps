"""Temporal workflow for Fabric workspace tag synchronization."""

from datetime import timedelta
from typing import Any, Callable, Dict, List, Sequence

from app.activities import FabricWorkspaceTaggerActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow
from temporalio.common import RetryPolicy

logger = get_logger(__name__)
workflow.logger = logger


@workflow.defn
class FabricWorkspaceTagSyncWorkflow(WorkflowInterface):
    """Workflow to sync workspace tags from Microsoft Fabric to Atlan.

    This workflow:
    1. Validates and loads workflow configuration
    2. Fetches workspace metadata from Fabric/Power BI Admin APIs
    3. Maps workspace data to Atlan tags (capacity, pillar, env, etc.)
    4. Updates PowerBIWorkspace assets in Atlan with namespace-scoped tags
    5. Returns a summary of the sync operation
    """

    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workspace tag sync workflow.

        Args:
            workflow_config: Configuration dictionary with:
                - fabric_tenant_id: Azure AD tenant ID
                - fabric_client_id: Service principal client ID
                - tag_namespace: Tag namespace prefix (e.g., 'capacity')
                - capacity_tag_key: Key for capacity tags
                - atlan_connection_qualified_name: Power BI connection QN in Atlan
                - workspace_filter_regex: Optional workspace name filter

        Returns:
            WorkspaceTagSyncResult dictionary with counts and errors
        """
        logger.info("Starting Fabric workspace tag sync workflow")

        activities_instance = FabricWorkspaceTaggerActivities()

        # Retry policy for transient failures
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            backoff_coefficient=2,
            initial_interval=timedelta(seconds=1),
        )

        # Step 1: Validate and load workflow args
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(seconds=30),
        )

        logger.info(
            f"Workflow config loaded: namespace={workflow_args.get('tag_namespace')}"
        )

        # Step 2: Fetch workspace metadata from Fabric
        workspaces: List[Dict[str, Any]] = (
            await workflow.execute_activity_method(
                activities_instance.fetch_fabric_workspaces,
                workflow_args,
                retry_policy=retry_policy,
                start_to_close_timeout=timedelta(minutes=10),
            )
        )

        logger.info(f"Fetched {len(workspaces)} workspaces from Fabric")

        if not workspaces:
            logger.warning("No workspaces fetched; workflow complete with no updates")
            return {
                "total_workspaces": 0,
                "workspaces_updated": 0,
                "workspaces_skipped": 0,
                "workspaces_failed": 0,
                "errors": [],
            }

        # Step 3: Update Atlan tags for all workspaces
        result: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.update_atlan_workspace_tags,
            workflow_args,
            workspaces,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=30),
        )

        logger.info(
            f"Workflow complete: {result.get('workspaces_updated')} updated, "
            f"{result.get('workspaces_failed')} failed"
        )

        return result

    @staticmethod
    def get_activities(
        activities: ActivitiesInterface,
    ) -> Sequence[Callable[..., Any]]:
        """Declare which activity methods are part of this workflow for the worker.

        Args:
            activities: Activities instance

        Returns:
            List of activity methods
        """
        if not isinstance(activities, FabricWorkspaceTaggerActivities):
            raise TypeError(
                "Activities must be an instance of FabricWorkspaceTaggerActivities"
            )

        return [
            activities.get_workflow_args,
            activities.fetch_fabric_workspaces,
            activities.update_atlan_workspace_tags,
        ]
