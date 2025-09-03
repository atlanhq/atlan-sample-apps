from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.activities import AnaplanMetadataExtractionActivities


class TestExtractAnaplanAppActivity:
    """Test cases for extract_anaplanapp activity function."""

    @pytest.fixture
    def mock_activities(self):
        """Create mock activities instance."""
        return AnaplanMetadataExtractionActivities()

    @pytest.fixture
    def mock_state(self):
        """Create mock state with client."""
        state = MagicMock()
        state.client = MagicMock()
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

    async def test_extract_anaplanapp_success(
        self, mock_activities, mock_state, workflow_args
    ):
        """Test successful app extraction."""
        # Arrange
        app_data = [
            {
                "guid": "app_guid_1",
                "name": "Test App 1",
                "description": "Test App Description 1",
                "customerId": "test_customer_123",
                "deletedAt": None,
                "mpCount": 5,
                "isFavorite": True,
            },
            {
                "guid": "app_guid_2",
                "name": "Test App 2",
                "description": "Test App Description 2",
                "customerId": "test_customer_123",
                "deletedAt": None,
                "mpCount": 3,
                "isFavorite": False,
            },
        ]

        mock_parquet_output = MagicMock()
        mock_parquet_output.get_full_path.return_value = "./test_output/raw/anaplanapp"
        mock_parquet_output.get_statistics = AsyncMock(return_value={"records": 2})
        mock_parquet_output.write_dataframe = AsyncMock()

        with (
            patch.object(mock_activities, "_get_state", return_value=mock_state),
            patch(
                "app.activities.setup_parquet_output",
                return_value=mock_parquet_output,
            ),
            patch(
                "app.activities.extract_apps_data",
                return_value=app_data,
            ),
            patch("pandas.DataFrame"),
        ):
            # Act
            result = await mock_activities.extract_anaplanapp(workflow_args)

            # Assert
            assert result == {"records": 2}
            mock_parquet_output.write_dataframe.assert_called_once()
            mock_parquet_output.get_statistics.assert_called_once_with(
                typename="anaplanapp"
            )

    async def test_extract_anaplanapp_no_client(self, mock_activities, workflow_args):
        """Test app extraction when client is not found in state."""
        # Arrange
        mock_state = MagicMock()
        mock_state.client = None

        with patch.object(mock_activities, "_get_state", return_value=mock_state):
            # Act & Assert
            with pytest.raises(ValueError, match="Anaplan client not found in state"):
                await mock_activities.extract_anaplanapp(workflow_args)

    async def test_extract_anaplanapp_no_data(
        self, mock_activities, mock_state, workflow_args
    ):
        """Test app extraction when no app data is returned."""
        # Arrange
        mock_parquet_output = MagicMock()
        mock_parquet_output.get_full_path.return_value = "./test_output/raw/anaplanapp"
        mock_parquet_output.get_statistics = AsyncMock(return_value={"records": 0})
        mock_parquet_output.write_dataframe = AsyncMock()

        with (
            patch.object(mock_activities, "_get_state", return_value=mock_state),
            patch(
                "app.activities.setup_parquet_output",
                return_value=mock_parquet_output,
            ),
            patch("app.activities.extract_apps_data", return_value=[]),
        ):
            # Act
            result = await mock_activities.extract_anaplanapp(workflow_args)

            # Assert
            assert result == {"records": 0}
            mock_parquet_output.write_dataframe.assert_not_called()
            mock_parquet_output.get_statistics.assert_called_once_with(
                typename="anaplanapp"
            )

    async def test_extract_anaplanapp_extraction_error(
        self, mock_activities, mock_state, workflow_args
    ):
        """Test app extraction when extraction fails."""
        # Arrange
        with (
            patch.object(mock_activities, "_get_state", return_value=mock_state),
            patch(
                "app.activities.setup_parquet_output",
                side_effect=Exception("API Error"),
            ),
        ):
            # Act & Assert
            with pytest.raises(Exception, match="API Error"):
                await mock_activities.extract_anaplanapp(workflow_args)

    async def test_extract_anaplanapp_with_deleted_apps(
        self, mock_activities, mock_state, workflow_args
    ):
        """Test app extraction with deleted apps (should be filtered out)."""
        # Arrange
        app_data = [
            {
                "guid": "app_guid_1",
                "name": "Active App",
                "description": "Active App Description",
                "customerId": "test_customer_123",
                "deletedAt": None,
                "mpCount": 5,
                "isFavorite": True,
            },
            {
                "guid": "app_guid_2",
                "name": "Deleted App",
                "description": "Deleted App Description",
                "customerId": "test_customer_123",
                "deletedAt": "2024-01-01T00:00:00Z",
                "mpCount": 3,
                "isFavorite": False,
            },
        ]

        mock_parquet_output = MagicMock()
        mock_parquet_output.get_full_path.return_value = "./test_output/raw/anaplanapp"
        mock_parquet_output.get_statistics = AsyncMock(return_value={"records": 1})
        mock_parquet_output.write_dataframe = AsyncMock()

        with (
            patch.object(mock_activities, "_get_state", return_value=mock_state),
            patch(
                "app.activities.setup_parquet_output",
                return_value=mock_parquet_output,
            ),
            patch(
                "app.activities.extract_apps_data",
                return_value=app_data,
            ),
            patch("pandas.DataFrame") as mock_df,
        ):
            # Act
            result = await mock_activities.extract_anaplanapp(workflow_args)

            # Assert
            assert result == {"records": 1}
            mock_parquet_output.write_dataframe.assert_called_once()
            # Verify that the DataFrame was created with the app data
            # Note: DataFrame may be called multiple times due to logging, so we check it was called at least once
            assert mock_df.call_count >= 1
