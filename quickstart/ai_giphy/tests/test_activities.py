from unittest.mock import Mock, patch

import pytest
from app.activities import AIGiphyActivities


class TestAIGiphyActivities:
    @pytest.fixture()
    def activities(self) -> AIGiphyActivities:
        return AIGiphyActivities()

    @staticmethod
    @pytest.mark.asyncio
    async def test_run_ai_agent_success(activities: AIGiphyActivities) -> None:
        """Test successful AI agent execution."""
        test_input = "Fetch a dog gif and send it to user@example.com"
        expected_output = {
            "output": "I've found a dog gif and sent it to user@example.com",
            "intermediate_steps": []
        }

        with patch("app.activities.get_chain") as mock_get_chain:
            mock_chain = Mock()
            mock_chain.invoke.return_value = expected_output
            mock_get_chain.return_value = mock_chain

            result = await activities.run_ai_agent(test_input)

            assert result == expected_output
            mock_get_chain.assert_called_once()
            mock_chain.invoke.assert_called_once_with({"input": test_input})

    @staticmethod
    @pytest.mark.asyncio
    async def test_run_ai_agent_failure(activities: AIGiphyActivities) -> None:
        """Test AI agent execution failure raises exception."""
        test_input = "Invalid input"

        with patch("app.activities.get_chain") as mock_get_chain:
            mock_chain = Mock()
            mock_chain.invoke.side_effect = Exception("AI Agent Error")
            mock_get_chain.return_value = mock_chain

            with pytest.raises(Exception, match="AI Agent Error"):
                await activities.run_ai_agent(test_input)

            mock_get_chain.assert_called_once()
            mock_chain.invoke.assert_called_once_with({"input": test_input})

    @staticmethod
    @pytest.mark.asyncio
    async def test_run_ai_agent_empty_input(activities: AIGiphyActivities) -> None:
        """Test AI agent with empty input string."""
        test_input = ""
        expected_output = {"output": "No action taken for empty input"}

        with patch("app.activities.get_chain") as mock_get_chain:
            mock_chain = Mock()
            mock_chain.invoke.return_value = expected_output
            mock_get_chain.return_value = mock_chain

            result = await activities.run_ai_agent(test_input)

            assert result == expected_output
            mock_get_chain.assert_called_once()
            mock_chain.invoke.assert_called_once_with({"input": test_input})

    @staticmethod
    @pytest.mark.asyncio
    async def test_run_ai_agent_get_chain_failure(activities: AIGiphyActivities) -> None:
        """Test AI agent execution when get_chain fails."""
        test_input = "Test input"

        with patch("app.activities.get_chain", side_effect=Exception("Chain creation failed")):
            with pytest.raises(Exception, match="Chain creation failed"):
                await activities.run_ai_agent(test_input)
