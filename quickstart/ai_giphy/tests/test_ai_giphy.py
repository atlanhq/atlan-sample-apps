from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.activities import AIGiphyActivities
from app.ai_agent import fetch_gif, send_email_with_gify
from app.workflow import AIGiphyWorkflow


class TestAIGiphyIntegration:
    """Integration tests for the AI Giphy application."""

    @pytest.fixture(scope="class", autouse=True)
    def mock_env_vars(self):
        """Mock environment variables for all tests in this class."""
        with (
            patch("app.ai_agent.GIPHY_API_KEY", "test_giphy_key"),
            patch("app.ai_agent.SMTP_HOST", "test.smtp.com"),
            patch("app.ai_agent.SMTP_PORT", "587"),
            patch("app.ai_agent.SMTP_USERNAME", "test_user"),
            patch("app.ai_agent.SMTP_PASSWORD", "test_password"),
            patch("os.environ.get") as mock_env_get,
        ):
            # Mock Azure OpenAI environment variables
            env_vars = {
                "APP_AZURE_OPENAI_API_KEY": "test_azure_key",
                "APP_AZURE_OPENAI_API_VERSION": "2023-05-15",
                "APP_AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "APP_AZURE_OPENAI_DEPLOYMENT_NAME": "test-deployment",
            }
            mock_env_get.side_effect = lambda key, default=None: env_vars.get(
                key, default
            )

            yield

    @pytest.fixture(scope="class")
    def workflow(self) -> AIGiphyWorkflow:
        return AIGiphyWorkflow()

    @pytest.fixture()
    def activities(self) -> AIGiphyActivities:
        return AIGiphyActivities()

    @staticmethod
    @pytest.mark.asyncio
    async def test_full_workflow_integration(
        workflow: AIGiphyWorkflow,
        activities: AIGiphyActivities,
    ) -> None:
        """Test the complete workflow from start to finish."""
        workflow_config = {"workflow_id": "integration_test"}
        workflow_args = {
            "ai_input_string": "Find a cute puppy gif and send it to user@example.com"
        }

        # Mock the AI agent chain response
        ai_agent_response = {
            "output": "I found a cute puppy gif and sent it to user@example.com successfully!",
            "intermediate_steps": [
                ("Searching for puppy gif...", "Found gif: https://test-puppy.gif"),
                ("Sending email...", "Email sent successfully to user@example.com"),
            ],
        }

        with (
            patch(
                "app.workflow.workflow.execute_activity_method", new_callable=AsyncMock
            ) as mock_get_args,
            patch(
                "app.workflow.workflow.execute_activity", new_callable=AsyncMock
            ) as mock_ai_activity,
            patch("app.activities.get_chain") as mock_get_chain,
        ):
            # Setup mocks
            mock_get_args.return_value = workflow_args
            mock_ai_activity.return_value = ai_agent_response

            mock_chain = Mock()
            mock_chain.invoke.return_value = ai_agent_response
            mock_get_chain.return_value = mock_chain

            # Execute workflow
            await workflow.run(workflow_config)

            # Verify workflow executed correctly
            mock_get_args.assert_called_once()
            mock_ai_activity.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_ai_agent_tools_integration() -> None:
        """Test the AI agent with its tools in isolation."""

        with (
            patch("requests.get") as mock_requests,
            patch("smtplib.SMTP") as mock_smtp,
            patch("app.ai_agent.AzureChatOpenAI"),
            patch("app.ai_agent.hub.pull"),
            patch("app.ai_agent.create_tool_calling_agent"),
            patch("app.ai_agent.AgentExecutor"),
        ):
            # Mock HTTP request for gif
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": {"images": {"original": {"url": "https://cat.gif"}}}
            }
            mock_response.raise_for_status.return_value = None
            mock_requests.return_value = mock_response

            # Mock SMTP
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Test fetch_gif function
            gif_url = fetch_gif("cat")
            assert gif_url == "https://cat.gif"

            # Test send_email_with_gify function
            email_result = send_email_with_gify("test@example.com", gif_url)
            assert email_result == "Email sent successfully"

            # Verify calls
            mock_requests.assert_called_once()
            mock_server.send_message.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_error_handling_integration(activities: AIGiphyActivities) -> None:
        """Test error handling throughout the application."""
        test_input = "Invalid request that should fail"

        with patch("app.activities.get_chain") as mock_get_chain:
            # Simulate chain creation failure
            mock_get_chain.side_effect = Exception("Failed to initialize AI agent")

            with pytest.raises(Exception, match="Failed to initialize AI agent"):
                await activities.run_ai_agent(test_input)

    @staticmethod
    def test_workflow_activities_configuration(
        workflow: AIGiphyWorkflow,
        activities: AIGiphyActivities,
    ) -> None:
        """Test that workflow is correctly configured with activities."""
        activity_methods = workflow.get_activities(activities)

        # Verify all required activities are present
        expected_activities = [
            activities.run_ai_agent,
            activities.get_workflow_args,
        ]

        assert len(activity_methods) == len(expected_activities)
        for expected_activity in expected_activities:
            assert expected_activity in activity_methods

    @staticmethod
    @pytest.mark.asyncio
    async def test_default_input_handling(workflow: AIGiphyWorkflow) -> None:
        """Test that workflow handles missing input correctly with defaults."""
        workflow_config = {"workflow_id": "default_test"}
        workflow_args = {}  # Empty args to trigger default

        with (
            patch(
                "app.workflow.workflow.execute_activity_method", new_callable=AsyncMock
            ) as mock_get_args,
            patch(
                "app.workflow.workflow.execute_activity", new_callable=AsyncMock
            ) as mock_ai_activity,
        ):
            mock_get_args.return_value = workflow_args
            mock_ai_activity.return_value = {"output": "Default execution completed"}

            await workflow.run(workflow_config)

            # Verify default input was used
            call_args = mock_ai_activity.call_args
            assert call_args[0][1] == "Fetch a cat gif and send it to test@example.com"
