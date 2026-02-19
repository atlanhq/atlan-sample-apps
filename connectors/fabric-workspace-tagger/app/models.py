"""Pydantic models for configuration and data payloads."""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration model loaded from workflow config."""

    fabric_tenant_id: str = Field(
        ...,
        description="Azure AD / Entra ID tenant ID for authentication",
    )
    fabric_client_id: str = Field(
        ...,
        description="Service principal client ID with Fabric Admin API access",
    )
    fabric_authority_url: str = Field(
        default="https://login.microsoftonline.com",
        description="Azure AD authority URL",
    )
    fabric_scope: str = Field(
        default="https://analysis.windows.net/powerbi/api/.default",
        description="OAuth scope for Power BI / Fabric APIs",
    )
    tag_namespace: str = Field(
        ...,
        description="Prefix/namespace for tags managed by this app (e.g., 'capacity', 'pillar')",
    )
    capacity_tag_key: str = Field(
        ...,
        description="Key to use for capacity tags (e.g., 'capacity')",
    )
    workspace_filter_regex: Optional[str] = Field(
        default=None,
        description="Optional regex filter to limit workspaces by name or ID",
    )
    atlan_connection_qualified_name: str = Field(
        ...,
        description="Qualified name of the Power BI connection in Atlan (e.g., 'default/powerbi/1234567890')",
    )

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow extra fields from workflow config


class FabricWorkspace(BaseModel):
    """Normalized workspace model from Fabric API."""

    id: str = Field(..., description="Workspace GUID")
    name: str = Field(..., description="Workspace display name")
    capacity_id: Optional[str] = Field(default=None, description="Capacity GUID")
    capacity_name: Optional[str] = Field(default=None, description="Capacity display name")
    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom tags extracted from workspace metadata",
    )
    state: Optional[str] = Field(default=None, description="Workspace state (Active, Deleted, etc.)")


class FabricCapacity(BaseModel):
    """Capacity model from Fabric/Power BI Admin API."""

    id: str = Field(..., description="Capacity GUID")
    display_name: str = Field(..., description="Capacity display name")
    sku: Optional[str] = Field(default=None, description="Capacity SKU (e.g., F2, P1)")
    region: Optional[str] = Field(default=None, description="Azure region")
    state: Optional[str] = Field(default=None, description="Capacity state")


class WorkspaceTagSyncResult(BaseModel):
    """Result summary for workspace tag synchronization."""

    total_workspaces: int = 0
    workspaces_updated: int = 0
    workspaces_skipped: int = 0
    workspaces_failed: int = 0
    errors: list[str] = Field(default_factory=list)
