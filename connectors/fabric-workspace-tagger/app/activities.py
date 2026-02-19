"""Temporal activities for fetching Fabric metadata and updating Atlan tags."""

import os
from typing import Any, Dict, List

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from pyatlan.client.atlan import AtlanClient
from pyatlan.model.assets import PowerBIWorkspace
from pyatlan.model.search import DSL, Term
from temporalio import activity

from app.fabric_client import FabricAPIClient
from app.models import AppConfig, FabricWorkspace, WorkspaceTagSyncResult

logger = get_logger(__name__)
activity.logger = logger


class FabricWorkspaceTaggerActivities(ActivitiesInterface):
    """Activities for Microsoft Fabric workspace tag synchronization."""

    @activity.defn
    async def get_workflow_args(
        self, workflow_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and validate workflow configuration.

        Args:
            workflow_config: Raw workflow config from Temporal

        Returns:
            Validated and merged workflow args
        """
        logger.info("Processing workflow configuration")

        # Merge config with any overrides
        # The workflow_config typically contains user inputs from the UI
        args = {**workflow_config}

        # Validate required fields
        required_fields = [
            "fabric_tenant_id",
            "fabric_client_id",
            "tag_namespace",
            "capacity_tag_key",
            "atlan_connection_qualified_name",
        ]

        missing = [f for f in required_fields if not args.get(f)]
        if missing:
            raise ValueError(f"Missing required configuration fields: {missing}")

        logger.info(
            f"Workflow args validated: tenant={args.get('fabric_tenant_id')}, "
            f"namespace={args.get('tag_namespace')}"
        )

        return args

    @activity.defn
    async def fetch_fabric_workspaces(
        self, config_dict: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch workspace metadata from Microsoft Fabric / Power BI Admin APIs.

        Args:
            config_dict: Application configuration dictionary

        Returns:
            List of serialized FabricWorkspace models
        """
        config = AppConfig(**config_dict)
        logger.info(
            f"Fetching Fabric workspaces for tenant {config.fabric_tenant_id}"
        )

        # Retrieve client secret from environment (set by Apps Framework secret store)
        client_secret = os.environ.get("FABRIC_CLIENT_SECRET")
        if not client_secret:
            raise ValueError(
                "FABRIC_CLIENT_SECRET not found in environment. "
                "Ensure it is configured in the app's secret store."
            )

        # Initialize Fabric API client
        fabric_client = FabricAPIClient(config=config, client_secret=client_secret)

        # Fetch workspaces
        workspaces = fabric_client.list_workspaces()

        logger.info(f"Fetched {len(workspaces)} workspaces from Fabric")

        # Serialize to dict for Temporal (Pydantic models are not directly serializable)
        return [ws.model_dump() for ws in workspaces]

    @activity.defn
    async def update_atlan_workspace_tags(
        self, config_dict: Dict[str, Any], workspaces_dict: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update Atlan PowerBIWorkspace assets with tags from Fabric.

        Args:
            config_dict: Application configuration dictionary
            workspaces_dict: List of serialized FabricWorkspace models

        Returns:
            Summary result of tag sync operation
        """
        config = AppConfig(**config_dict)
        workspaces = [FabricWorkspace(**ws) for ws in workspaces_dict]

        logger.info(
            f"Updating Atlan tags for {len(workspaces)} workspaces "
            f"in namespace '{config.tag_namespace}'"
        )

        # Initialize Atlan client (Apps Framework injects credentials)
        client = AtlanClient()

        result = WorkspaceTagSyncResult(total_workspaces=len(workspaces))

        for ws in workspaces:
            try:
                # Resolve PowerBIWorkspace in Atlan
                atlan_workspace = self._resolve_workspace_in_atlan(
                    client=client,
                    workspace_id=ws.id,
                    workspace_name=ws.name,
                    connection_qn=config.atlan_connection_qualified_name,
                )

                if not atlan_workspace:
                    logger.warning(
                        f"Workspace {ws.name} (ID: {ws.id}) not found in Atlan; skipping"
                    )
                    result.workspaces_skipped += 1
                    continue

                # Compute desired tags
                desired_tags = self._compute_desired_tags(config=config, workspace=ws)

                # Update tags if changed
                updated = self._update_workspace_tags(
                    client=client,
                    workspace=atlan_workspace,
                    desired_tags=desired_tags,
                    tag_namespace=config.tag_namespace,
                )

                if updated:
                    result.workspaces_updated += 1
                    logger.info(
                        f"Updated tags for workspace {ws.name}: {desired_tags}"
                    )
                else:
                    result.workspaces_skipped += 1

            except Exception as e:
                logger.error(
                    f"Failed to update workspace {ws.name}: {e}", exc_info=True
                )
                result.workspaces_failed += 1
                result.errors.append(f"{ws.name}: {str(e)}")

        logger.info(
            f"Tag sync complete: {result.workspaces_updated} updated, "
            f"{result.workspaces_skipped} skipped, {result.workspaces_failed} failed"
        )

        return result.model_dump()

    def _resolve_workspace_in_atlan(
        self,
        client: AtlanClient,
        workspace_id: str,
        workspace_name: str,
        connection_qn: str,
    ) -> PowerBIWorkspace | None:
        """Resolve PowerBIWorkspace asset in Atlan by workspace ID.

        The qualifiedName for PowerBIWorkspace typically follows the pattern:
        <connection_qn>/<workspace_name>

        We search by both qualifiedName pattern and workspace ID to handle variations.

        Args:
            client: Atlan client
            workspace_id: Fabric workspace GUID
            workspace_name: Workspace display name
            connection_qn: Connection qualified name prefix

        Returns:
            PowerBIWorkspace asset or None if not found
        """
        # Attempt 1: Search by qualifiedName pattern
        # PowerBIWorkspace qualified names typically: default/powerbi/1234567890/WorkspaceName
        qn_pattern = f"{connection_qn}/{workspace_name}"

        try:
            dsl = DSL(
                query=Term(field="qualifiedName", value=qn_pattern),
            )
            results = client.asset.search(dsl=dsl)

            if results and len(results) > 0:
                for asset in results:
                    if isinstance(asset, PowerBIWorkspace):
                        logger.debug(
                            f"Resolved workspace {workspace_name} by qualifiedName"
                        )
                        return asset
        except Exception as e:
            logger.debug(
                f"Search by qualifiedName failed for {workspace_name}: {e}"
            )

        # Attempt 2: Search by name and type
        try:
            dsl = DSL(
                query=Term(field="name.keyword", value=workspace_name),
            )
            results = client.asset.search(dsl=dsl)

            if results and len(results) > 0:
                for asset in results:
                    if (
                        isinstance(asset, PowerBIWorkspace)
                        and asset.connection_qualified_name == connection_qn
                    ):
                        logger.debug(
                            f"Resolved workspace {workspace_name} by name search"
                        )
                        return asset
        except Exception as e:
            logger.debug(f"Search by name failed for {workspace_name}: {e}")

        logger.warning(
            f"Could not resolve workspace {workspace_name} (ID: {workspace_id}) in Atlan"
        )
        return None

    def _compute_desired_tags(
        self, config: AppConfig, workspace: FabricWorkspace
    ) -> set[str]:
        """Compute the set of Atlan tags that should be applied to this workspace.

        Tags are namespaced with the configured namespace, e.g.:
        - capacity:Fabric-Critical-01
        - pillar:Manufacturing

        Args:
            config: Application configuration
            workspace: Fabric workspace model

        Returns:
            Set of tag strings (namespaced)
        """
        tags = set()

        # Add capacity tag if available
        if workspace.capacity_name:
            capacity_tag = f"{config.capacity_tag_key}:{workspace.capacity_name}"
            tags.add(capacity_tag)

        # Add custom tags from workspace metadata
        for key, value in workspace.tags.items():
            tag = f"{key}:{value}"
            tags.add(tag)

        return tags

    def _update_workspace_tags(
        self,
        client: AtlanClient,
        workspace: PowerBIWorkspace,
        desired_tags: set[str],
        tag_namespace: str,
    ) -> bool:
        """Update assetTags on a PowerBIWorkspace asset.

        This method:
        1. Reads existing tags
        2. Removes any tags in the managed namespace
        3. Adds the desired tags
        4. Persists the update if tags changed

        Args:
            client: Atlan client
            workspace: PowerBIWorkspace asset
            desired_tags: Set of desired tag strings
            tag_namespace: Namespace prefix for managed tags

        Returns:
            True if tags were updated, False if no change needed
        """
        existing_tags = set(workspace.atlan_tags or [])

        # Identify tags in our managed namespace
        managed_tags = {
            tag
            for tag in existing_tags
            if tag.split(":")[0] in [tag_namespace, "capacity", "pillar", "env"]
            # This assumes managed tags use colon-delimited format
        }

        # Compute new tag set: unmanaged tags + desired tags
        new_tags = (existing_tags - managed_tags) | desired_tags

        # Check if tags changed
        if new_tags == existing_tags:
            logger.debug(f"No tag changes for workspace {workspace.name}")
            return False

        # Update tags using pyatlan
        # Note: We use the updater pattern to avoid full asset replacement
        try:
            updater = PowerBIWorkspace.updater(
                qualified_name=workspace.qualified_name,
                name=workspace.name,
            )
            updater.atlan_tags = list(new_tags)

            response = client.asset.save(updater)

            if response and response.assets_updated(PowerBIWorkspace):
                logger.info(
                    f"Successfully updated tags for {workspace.name}: "
                    f"{len(new_tags)} total tags"
                )
                return True
            else:
                logger.warning(
                    f"Tag update for {workspace.name} returned no assets updated"
                )
                return False

        except Exception as e:
            logger.error(
                f"Failed to save tags for {workspace.name}: {e}", exc_info=True
            )
            raise
