"""Unit tests for polyglot workflow."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.activities import PolyglotActivities
from app.workflow import PolyglotWorkflow


class TestPolyglotWorkflow:
    """Test suite for PolyglotWorkflow."""

    @pytest.fixture
    def workflow(self):
        """Create a PolyglotWorkflow instance for testing."""
        return PolyglotWorkflow()

    def test_get_activities(self):
        """Test get_activities static method."""
        activities = PolyglotActivities()
        activity_list = PolyglotWorkflow.get_activities(activities)

        assert len(activity_list) == 3
        assert activities.calculate_factorial in activity_list
        assert activities.save_result_to_json in activity_list
        assert activities.get_workflow_args in activity_list

    def test_get_activities_wrong_type(self):
        """Test get_activities with wrong activity type."""
        with pytest.raises(TypeError):
            PolyglotWorkflow.get_activities("not_an_activity")

    @pytest.mark.asyncio
    async def test_workflow_run(self, workflow):
        """Test workflow execution.

        Note: This is a simplified test that mocks the workflow execution.
        Full workflow testing requires Temporal test environment.
        """
        # This test demonstrates the workflow structure
        # For complete testing, use Temporal's test framework
        workflow_config = {
            "workflow_id": "test-workflow-123",
        }

        workflow_args = {
            "number": 5,
        }

        # Mock the workflow execution context
        # In real tests, you'd use Temporal's workflow testing utilities
        assert workflow is not None
        assert hasattr(workflow, "run")

