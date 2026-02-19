"""Unit tests for Pydantic models."""

import pytest
from app.models import AppConfig, FabricWorkspace, WorkspaceTagSyncResult


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_app_config_required_fields(self):
        """Test that AppConfig validates required fields."""
        with pytest.raises(Exception):
            AppConfig()

    def test_app_config_with_minimal_fields(self):
        """Test AppConfig creation with minimal required fields."""
        config = AppConfig(
            fabric_tenant_id="tenant-123",
            fabric_client_id="client-456",
            tag_namespace="capacity",
            capacity_tag_key="capacity",
            atlan_connection_qualified_name="default/powerbi/123",
        )
        assert config.fabric_tenant_id == "tenant-123"
        assert config.fabric_authority_url == "https://login.microsoftonline.com"

    def test_app_config_with_all_fields(self):
        """Test AppConfig creation with all fields."""
        config = AppConfig(
            fabric_tenant_id="tenant-123",
            fabric_client_id="client-456",
            fabric_authority_url="https://custom-authority.com",
            fabric_scope="https://custom-scope/.default",
            tag_namespace="pillar",
            capacity_tag_key="cap",
            atlan_connection_qualified_name="default/powerbi/123",
            workspace_filter_regex="^Manufacturing.*",
        )
        assert config.fabric_authority_url == "https://custom-authority.com"
        assert config.workspace_filter_regex == "^Manufacturing.*"


class TestFabricWorkspace:
    """Tests for FabricWorkspace model."""

    def test_fabric_workspace_minimal(self):
        """Test FabricWorkspace creation with minimal fields."""
        ws = FabricWorkspace(id="ws-123", name="Test Workspace")
        assert ws.id == "ws-123"
        assert ws.name == "Test Workspace"
        assert ws.capacity_name is None
        assert ws.tags == {}

    def test_fabric_workspace_with_capacity(self):
        """Test FabricWorkspace creation with capacity info."""
        ws = FabricWorkspace(
            id="ws-123",
            name="Test Workspace",
            capacity_id="cap-456",
            capacity_name="Production Capacity",
        )
        assert ws.capacity_id == "cap-456"
        assert ws.capacity_name == "Production Capacity"

    def test_fabric_workspace_with_tags(self):
        """Test FabricWorkspace creation with custom tags."""
        ws = FabricWorkspace(
            id="ws-123",
            name="Test Workspace",
            tags={"pillar": "Manufacturing", "env": "prod"},
        )
        assert ws.tags["pillar"] == "Manufacturing"
        assert ws.tags["env"] == "prod"


class TestWorkspaceTagSyncResult:
    """Tests for WorkspaceTagSyncResult model."""

    def test_sync_result_defaults(self):
        """Test default values for sync result."""
        result = WorkspaceTagSyncResult()
        assert result.total_workspaces == 0
        assert result.workspaces_updated == 0
        assert result.errors == []

    def test_sync_result_with_data(self):
        """Test sync result with actual data."""
        result = WorkspaceTagSyncResult(
            total_workspaces=10,
            workspaces_updated=8,
            workspaces_skipped=1,
            workspaces_failed=1,
            errors=["Workspace X: Authentication failed"],
        )
        assert result.total_workspaces == 10
        assert result.workspaces_updated == 8
        assert len(result.errors) == 1
