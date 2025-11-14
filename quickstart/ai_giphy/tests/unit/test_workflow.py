from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.activities import AIGiphyActivities
from app.workflow import AIGiphyWorkflow


class TestAIGiphyWorkflow:
    @pytest.fixture(scope="class")
    def workflow(self) -> AIGiphyWorkflow:
        return AIGiphyWorkflow()

    @pytest.fixture()
    def activities(self) -> AIGiphyActivities:
        return AIGiphyActivities()

    @staticmethod
    @pytest.mark.asyncio
    async def test_workflow_run_success(workflow: AIGiphyWorkflow) -> None:
        """Test successful workflow execution with default input."""
        workflow_config = {"workflow_id": "test_workflow_123"}
        workflow_args = {
            "ai_input_string": "Find a cute cat gif and send it to test@example.com"
        }
        agent_output = {
            "output": "I've found a cute cat gif and sent it to test@example.com successfully!",
            "intermediate_steps": [],
        }

        with (
            patch(
                "app.workflow.workflow.execute_activity_method", new_callable=AsyncMock
            ) as mock_get_args,
            patch(
                "app.workflow.workflow.execute_activity", new_callable=AsyncMock
            ) as mock_execute_activity,
        ):
            mock_get_args.return_value = workflow_args
            mock_execute_activity.return_value = agent_output

            # This should complete without exceptions
            await workflow.run(workflow_config)

            # Verify the activities were called correctly
            mock_get_args.assert_called_once()
            mock_execute_activity.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_workflow_run_with_default_input(workflow: AIGiphyWorkflow) -> None:
        """Test workflow execution with default input when ai_input_string is not provided."""
        workflow_config = {"workflow_id": "test_workflow_456"}
        workflow_args = {}  # No ai_input_string provided
        agent_output = {
            "output": "I've found a cat gif and sent it to test@example.com using the default input!",
            "intermediate_steps": [],
        }

        with (
            patch(
                "app.workflow.workflow.execute_activity_method", new_callable=AsyncMock
            ) as mock_get_args,
            patch(
                "app.workflow.workflow.execute_activity", new_callable=AsyncMock
            ) as mock_execute_activity,
        ):
            mock_get_args.return_value = workflow_args
            mock_execute_activity.return_value = agent_output

            await workflow.run(workflow_config)

            # Verify default input was used
            mock_execute_activity.assert_called_once()
            # The call should use the default input string
            call_args = mock_execute_activity.call_args
            assert call_args[0][1] == "Fetch a cat gif and send it to test@example.com"

    @staticmethod
    @pytest.mark.asyncio
    async def test_workflow_run_activity_failure(workflow: AIGiphyWorkflow) -> None:
        """Test workflow handling when get_workflow_args activity fails."""
        workflow_config = {"workflow_id": "test_workflow_789"}

        with patch(
            "app.workflow.workflow.execute_activity_method", new_callable=AsyncMock
        ) as mock_get_args:
            mock_get_args.side_effect = Exception("Failed to get workflow args")

            with pytest.raises(Exception, match="Failed to get workflow args"):
                await workflow.run(workflow_config)

    @staticmethod
    @pytest.mark.asyncio
    async def test_workflow_run_ai_agent_failure(workflow: AIGiphyWorkflow) -> None:
        """Test workflow handling when AI agent activity fails."""
        workflow_config = {"workflow_id": "test_workflow_101"}
        workflow_args = {"ai_input_string": "Test input"}

        with (
            patch(
                "app.workflow.workflow.execute_activity_method", new_callable=AsyncMock
            ) as mock_get_args,
            patch(
                "app.workflow.workflow.execute_activity", new_callable=AsyncMock
            ) as mock_execute_activity,
        ):
            mock_get_args.return_value = workflow_args
            mock_execute_activity.side_effect = Exception("AI Agent execution failed")

            with pytest.raises(Exception, match="AI Agent execution failed"):
                await workflow.run(workflow_config)

    @staticmethod
    def test_get_activities_success(
        workflow: AIGiphyWorkflow, activities: AIGiphyActivities
    ) -> None:
        """Test get_activities returns correct activity methods."""
        activity_methods = workflow.get_activities(activities)

        assert len(activity_methods) == 2
        assert activities.run_ai_agent in activity_methods
        assert activities.get_workflow_args in activity_methods

    @staticmethod
    def test_get_activities_wrong_type(workflow: AIGiphyWorkflow) -> None:
        """Test get_activities raises TypeError for wrong activities type."""
        wrong_activities = Mock()  # Not an AIGiphyActivities instance

        with pytest.raises(
            TypeError, match="Activities must be an instance of AIGiphyActivities"
        ):
            workflow.get_activities(wrong_activities)

    @staticmethod
    @pytest.mark.asyncio
    async def test_workflow_run_custom_input(workflow: AIGiphyWorkflow) -> None:
        """Test workflow execution with custom ai_input_string."""
        workflow_config = {"workflow_id": "test_workflow_custom"}
        custom_input = "Find a funny dog gif and send it to custom@example.com"
        workflow_args = {"ai_input_string": custom_input}
        agent_output = {"output": f"Executed: {custom_input}", "intermediate_steps": []}

        with (
            patch(
                "app.workflow.workflow.execute_activity_method", new_callable=AsyncMock
            ) as mock_get_args,
            patch(
                "app.workflow.workflow.execute_activity", new_callable=AsyncMock
            ) as mock_execute_activity,
        ):
            mock_get_args.return_value = workflow_args
            mock_execute_activity.return_value = agent_output

            await workflow.run(workflow_config)

            # Verify custom input was used
            mock_execute_activity.assert_called_once()
            call_args = mock_execute_activity.call_args
            assert call_args[0][1] == custom_input
