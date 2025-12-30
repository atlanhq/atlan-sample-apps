from unittest.mock import Mock, patch

import pytest
from app.ai_agent import fetch_gif, get_chain, send_email_with_gify


class TestAIAgent:
    @pytest.fixture(scope="class", autouse=True)
    def mock_env_vars(self):
        """Mock environment variables for all tests in this class."""
        with (
            patch("app.ai_agent.GIPHY_API_KEY", "test_giphy_key"),
            patch("app.ai_agent.SMTP_HOST", "test.smtp.com"),
            patch("app.ai_agent.SMTP_PORT", "587"),
            patch("app.ai_agent.SMTP_USERNAME", "test_user"),
            patch("app.ai_agent.SMTP_PASSWORD", "test_password"),
            patch("app.ai_agent.OPENAI_API_KEY", "test_openai_key"),
            patch("app.ai_agent.OPENAI_MODEL_NAME", "gpt-4.1-mini"),
            patch("app.ai_agent.OPENAI_BASE_URL", None),
            patch("app.ai_agent.os.getenv") as mock_getenv,
        ):
            # Mock os.getenv for get_chain() function
            def getenv_side_effect(key, default=None):
                env_vars = {
                    "OPENAI_API_KEY": "test_openai_key",
                    "OPENAI_MODEL_NAME": "gpt-4.1-mini",
                    "OPENAI_BASE_URL": None,
                }
                return env_vars.get(key, default)

            mock_getenv.side_effect = getenv_side_effect

            yield

    @staticmethod
    def test_fetch_gif_success() -> None:
        """Test successful GIF fetching with a valid search term."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": {"images": {"original": {"url": "https://test.gif"}}}
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = fetch_gif("test")
            assert result == "https://test.gif"
            mock_get.assert_called_once()

    @staticmethod
    def test_fetch_gif_failure() -> None:
        """Test GIF fetching failure returns fallback GIF."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("API Error")

            result = fetch_gif("test")
            assert (
                result == "https://media.giphy.com/media/3o7abAHdYvZdBNnGZq/giphy.gif"
            )
            mock_get.assert_called_once()

    @staticmethod
    def test_send_email_with_gify_success() -> None:
        """Test successful email sending with valid configuration."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = send_email_with_gify("test@example.com", "https://test.gif")

            assert result == "Email sent successfully"
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()

    @staticmethod
    def test_send_email_with_gify_failure() -> None:
        """Test email sending failure returns error message."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP Error")

            result = send_email_with_gify("test@example.com", "https://test.gif")

            assert result == "Failed to send email"
            mock_smtp.assert_called_once()

    @staticmethod
    def test_get_chain_success() -> None:
        """Test successful creation of AI agent chain."""
        with (
            patch("app.ai_agent.ChatOpenAI") as mock_llm,
            patch("app.ai_agent.hub.pull") as mock_hub_pull,
            patch("app.ai_agent.create_tool_calling_agent") as mock_create_agent,
            patch("app.ai_agent.AgentExecutor") as mock_agent_executor,
        ):
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance

            mock_prompt = Mock()
            mock_hub_pull.return_value = mock_prompt

            mock_agent = Mock()
            mock_create_agent.return_value = mock_agent

            mock_executor = Mock()
            mock_agent_executor.return_value = mock_executor

            result = get_chain()

            assert result == mock_executor
            mock_llm.assert_called_once_with(
                api_key="test_openai_key",
                model="gpt-4.1-mini",
                base_url=None,
            )
            mock_hub_pull.assert_called_once_with("hwchase17/openai-tools-agent")
            mock_create_agent.assert_called_once()
            mock_agent_executor.assert_called_once()

    @staticmethod
    def test_get_chain_failure() -> None:
        """Test get_chain raises exception when agent creation fails."""
        with (
            patch("app.ai_agent.ChatOpenAI"),
            patch("app.ai_agent.hub.pull", side_effect=Exception("Hub Error")),
        ):
            with pytest.raises(Exception, match="Hub Error"):
                get_chain()
