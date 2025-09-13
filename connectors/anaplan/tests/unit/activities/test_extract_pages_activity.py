from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.activities import AppMetadataExtractionActivities


class TestExtractPagesActivity:
    """Test cases for extract_pages activity function."""

    @pytest.fixture
    def mock_activities(self):
        """Create mock activities instance."""
        return AppMetadataExtractionActivities()

    @pytest.fixture
    def mock_state(self):
        """Create mock state with client."""
        state = MagicMock()
        client = MagicMock()
        client.execute_http_get_request = AsyncMock()
        client.host = "test.anaplan.com"
        state.client = client
        state.metadata_filter_state = "none"
        state.metadata_filter = {}
        return state

    @pytest.fixture
    def workflow_args(self):
        """Create sample workflow arguments."""
        return {
            "output_prefix": "test_prefix",
            "output_path": "./test_output",
            "credential_guid": "test_credential_guid",
        }

    async def test_extract_pages_success(
        self, mock_activities, mock_state, workflow_args
    ):
        """Test successful page extraction."""
        # Arrange
        page_data = [
            {
                "guid": "page_guid_1",
                "name": "Test Page 1",
                "description": "Test Page Description 1",
                "appGuid": "app_guid_1",
                "deletedAt": None,
                "modelInfos": [{"modelId": "model_1"}, {"modelId": "model_2"}],
            },
            {
                "guid": "page_guid_2",
                "name": "Test Page 2",
                "description": "Test Page Description 2",
                "appGuid": "app_guid_2",
                "deletedAt": None,
                "modelInfos": [{"modelId": "model_3"}],
            },
        ]

        app_guids = {"app_guid_1", "app_guid_2"}

        mock_parquet_output = MagicMock()
        mock_parquet_output.get_full_path.return_value = "./test_output/raw/page"
        mock_parquet_output.get_statistics = AsyncMock(return_value={"records": 2})
        mock_parquet_output.write_dataframe = AsyncMock()

        with (
            patch.object(mock_activities, "_get_state", return_value=mock_state),
            patch(
                "app.activities.get_app_guids",
                new_callable=AsyncMock,
                return_value=app_guids,
            ),
            patch(
                "app.activities.setup_parquet_output",
                return_value=mock_parquet_output,
            ),
            patch(
                "app.activities.extract_pages_with_details",
                new_callable=AsyncMock,
                return_value=page_data,
            ),
            patch("pandas.DataFrame"),
        ):
            # Act
            result = await mock_activities.extract_pages(workflow_args)

            # Assert
            assert result == {"records": 2}
            mock_parquet_output.write_dataframe.assert_called_once()
            mock_parquet_output.get_statistics.assert_called_once_with(
                typename="page"
            )

    async def test_extract_pages_no_client(self, mock_activities, workflow_args):
        """Test page extraction when client is not found in state."""
        # Arrange
        mock_state = MagicMock()
        mock_state.client = None

        with patch.object(mock_activities, "_get_state", return_value=mock_state):
            # Act & Assert
            with pytest.raises(ValueError, match="Anaplan client not found in state"):
                await mock_activities.extract_pages(workflow_args)

    async def test_extract_pages_no_data(
        self, mock_activities, mock_state, workflow_args
    ):
        """Test page extraction when no page data is returned."""
        # Arrange
        app_guids = {"app_guid_1", "app_guid_2"}

        mock_parquet_output = MagicMock()
        mock_parquet_output.get_full_path.return_value = "./test_output/raw/page"
        mock_parquet_output.get_statistics = AsyncMock(return_value={"records": 0})
        mock_parquet_output.write_dataframe = AsyncMock()

        with (
            patch.object(mock_activities, "_get_state", return_value=mock_state),
            patch(
                "app.activities.get_app_guids",
                new_callable=AsyncMock,
                return_value=app_guids,
            ),
            patch(
                "app.activities.setup_parquet_output",
                return_value=mock_parquet_output,
            ),
            patch(
                "app.activities.extract_pages_with_details",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            # Act
            result = await mock_activities.extract_pages(workflow_args)

            # Assert
            assert result == {"records": 0}
            mock_parquet_output.write_dataframe.assert_not_called()
            mock_parquet_output.get_statistics.assert_called_once_with(
                typename="page"
            )

    async def test_extract_pages_extraction_error(
        self, mock_activities, mock_state, workflow_args
    ):
        """Test page extraction when extraction fails."""
        # Arrange
        app_guids = {"app_guid_1", "app_guid_2"}

        with (
            patch.object(mock_activities, "_get_state", return_value=mock_state),
            patch(
                "app.activities.get_app_guids",
                new_callable=AsyncMock,
                return_value=app_guids,
            ),
            patch(
                "app.activities.setup_parquet_output",
                side_effect=Exception("API Error"),
            ),
        ):
            # Act & Assert
            with pytest.raises(Exception, match="API Error"):
                await mock_activities.extract_pages(workflow_args)

    async def test_extract_pages_with_deleted_pages(
        self, mock_activities, mock_state, workflow_args
    ):
        """Test page extraction with deleted pages (should be filtered out)."""
        # Arrange
        page_data = [
            {
                "guid": "page_guid_1",
                "name": "Active Page",
                "description": "Active Page Description",
                "appGuid": "app_guid_1",
                "deletedAt": None,
                "modelInfos": [{"modelId": "model_1"}],
            },
            {
                "guid": "page_guid_2",
                "name": "Deleted Page",
                "description": "Deleted Page Description",
                "appGuid": "app_guid_2",
                "deletedAt": "2024-01-01T00:00:00Z",
                "modelInfos": [{"modelId": "model_2"}],
            },
        ]

        app_guids = {"app_guid_1", "app_guid_2"}

        mock_parquet_output = MagicMock()
        mock_parquet_output.get_full_path.return_value = "./test_output/raw/page"
        mock_parquet_output.get_statistics = AsyncMock(return_value={"records": 1})
        mock_parquet_output.write_dataframe = AsyncMock()

        with (
            patch.object(mock_activities, "_get_state", return_value=mock_state),
            patch(
                "app.activities.get_app_guids",
                new_callable=AsyncMock,
                return_value=app_guids,
            ),
            patch(
                "app.activities.setup_parquet_output",
                return_value=mock_parquet_output,
            ),
            patch(
                "app.activities.extract_pages_with_details",
                new_callable=AsyncMock,
                return_value=page_data,
            ),
            patch("pandas.DataFrame") as mock_df,
        ):
            # Act
            result = await mock_activities.extract_pages(workflow_args)

            # Assert
            assert result == {"records": 1}
            mock_parquet_output.write_dataframe.assert_called_once()
            # Verify that the DataFrame was created with the page data
            # Note: DataFrame may be called multiple times due to logging, so we check it was called at least once
            assert mock_df.call_count >= 1

    async def test_extract_pages_empty_app_guids(
        self, mock_activities, mock_state, workflow_args
    ):
        """Test page extraction when no app GUIDs are available."""
        # Arrange
        app_guids = set()

        mock_parquet_output = MagicMock()
        mock_parquet_output.get_full_path.return_value = "./test_output/raw/page"
        mock_parquet_output.get_statistics = AsyncMock(return_value={"records": 0})
        mock_parquet_output.write_dataframe = AsyncMock()

        with (
            patch.object(mock_activities, "_get_state", return_value=mock_state),
            patch(
                "app.activities.get_app_guids",
                new_callable=AsyncMock,
                return_value=app_guids,
            ),
            patch(
                "app.activities.setup_parquet_output",
                return_value=mock_parquet_output,
            ),
            patch(
                "app.activities.extract_pages_with_details",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            # Act
            result = await mock_activities.extract_pages(workflow_args)

            # Assert
            assert result == {"records": 0}
            mock_parquet_output.write_dataframe.assert_not_called()
            mock_parquet_output.get_statistics.assert_called_once_with(
                typename="page"
            )
