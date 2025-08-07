from unittest.mock import Mock, patch

import pytest
from activities import GiphyActivities
from workflow import GiphyWorkflow


class TestGiphyWorkflowWorker:
    @pytest.fixture(scope="class")
    def workflow(self) -> GiphyWorkflow:
        return GiphyWorkflow()

    @pytest.fixture()
    def activities(self) -> GiphyActivities:
        return GiphyActivities()

    @staticmethod
    @pytest.mark.asyncio
    async def test_fetch_gif_success(activities: GiphyActivities) -> None:
        """Test successful GIF fetching with a valid search term."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": {"images": {"original": {"url": "https://test.gif"}}}
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await activities.fetch_gif("test")
            assert result == "https://test.gif"
            mock_get.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_fetch_gif_failure(activities: GiphyActivities) -> None:
        """Test GIF fetching failure returns fallback GIF."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("API Error")

            result = await activities.fetch_gif("test")
            assert (
                result == "https://media.giphy.com/media/3o7abAHdYvZdBNnGZq/giphy.gif"
            )
            mock_get.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_send_email_success(activities: GiphyActivities) -> None:
        """Test successful email sending with valid configuration."""
        config = {
            "gif_url": "https://test.gif",
            "recipients": "test@example.com, test2@example.com",
        }

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            await activities.send_email(config)

            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_send_email_no_recipients(activities: GiphyActivities) -> None:
        """Test email sending with no valid recipients raises ValueError."""
        config = {"gif_url": "https://test.gif", "recipients": ""}

        with pytest.raises(ValueError, match="No valid recipients provided"):
            await activities.send_email(config)

    @staticmethod
    @pytest.mark.asyncio
    async def test_send_email_empty_recipients(
        activities: GiphyActivities,
    ) -> None:
        """Test email sending with only whitespace recipients raises ValueError."""
        config = {"gif_url": "https://test.gif", "recipients": "  ,  ,  "}

        with pytest.raises(ValueError, match="No valid recipients provided"):
            await activities.send_email(config)
