from unittest.mock import MagicMock, patch

import pytest
from app.utils import setup_parquet_output, should_include_asset


class TestUtils:
    """Test cases for utils functions."""

    @patch("app.utils.ParquetFileWriter")
    def test_setup_parquet_output_success(self, mock_parquet_output):
        """Test successful parquet output setup."""
        # Arrange
        workflow_args = {
            "output_path": "/test/path",
        }
        output_suffix = "test_suffix"

        mock_output_instance = MagicMock()
        mock_parquet_output.return_value = mock_output_instance

        # Act
        result = setup_parquet_output(workflow_args, output_suffix)

        # Assert
        assert result == mock_output_instance
        mock_parquet_output.assert_called_once_with(
            path="/test/path/test_suffix",
        )

    def test_setup_parquet_output_missing_path(self):
        """Test parquet output setup with missing output_path."""
        # Arrange
        workflow_args = {}
        output_suffix = "test_suffix"

        # Act & Assert
        with pytest.raises(
            ValueError, match="Output path must be specified in workflow_args"
        ):
            setup_parquet_output(workflow_args, output_suffix)

    def test_setup_parquet_output_empty_args(self):
        """Test parquet output setup with empty workflow_args."""
        # Arrange
        workflow_args = {}
        output_suffix = "test_suffix"

        # Act & Assert
        with pytest.raises(
            ValueError, match="Output path must be specified in workflow_args"
        ):
            setup_parquet_output(workflow_args, output_suffix)

    def test_should_include_asset_none_filter_state(self):
        """Test should_include_asset with 'none' filter state."""
        # Arrange
        asset_data = {"guid": "test_guid"}
        typename = "app"
        metadata_filter_state = "none"
        metadata_filter = {"app_1": []}

        # Act
        result = should_include_asset(
            asset_data, typename, metadata_filter_state, metadata_filter
        )

        # Assert
        assert result is True

    def test_should_include_asset_empty_filter(self):
        """Test should_include_asset with empty filter."""
        # Arrange
        asset_data = {"guid": "test_guid"}
        typename = "app"
        metadata_filter_state = "include"
        metadata_filter = {}

        # Act
        result = should_include_asset(
            asset_data, typename, metadata_filter_state, metadata_filter
        )

        # Assert
        assert result is True

    def test_should_include_asset_app_include(self):
        """Test should_include_asset for app with include filter."""
        # Arrange
        asset_data = {"guid": "app_1"}
        typename = "app"
        metadata_filter_state = "include"
        metadata_filter = {"app_1": [], "app_2": []}

        # Act
        result = should_include_asset(
            asset_data, typename, metadata_filter_state, metadata_filter
        )

        # Assert
        assert result is True

    def test_should_include_asset_app_exclude(self):
        """Test should_include_asset for app with exclude filter."""
        # Arrange
        asset_data = {"guid": "app_1"}
        typename = "app"
        metadata_filter_state = "exclude"
        metadata_filter = {"app_1": [], "app_2": []}

        # Act
        result = should_include_asset(
            asset_data, typename, metadata_filter_state, metadata_filter
        )

        # Assert
        assert result is False

    def test_should_include_asset_page_include(self):
        """Test should_include_asset for page with include filter."""
        # Arrange
        asset_data = {"appGuid": "app_1", "guid": "page_1"}
        typename = "page"
        metadata_filter_state = "include"
        metadata_filter = {"app_1": ["page_1"]}

        # Act
        result = should_include_asset(
            asset_data, typename, metadata_filter_state, metadata_filter
        )

        # Assert
        assert result is True

    def test_should_include_asset_page_exclude(self):
        """Test should_include_asset for page with exclude filter."""
        # Arrange
        asset_data = {"appGuid": "app_1", "guid": "page_1"}
        typename = "page"
        metadata_filter_state = "exclude"
        metadata_filter = {"app_1": ["page_1"]}

        # Act
        result = should_include_asset(
            asset_data, typename, metadata_filter_state, metadata_filter
        )

        # Assert
        assert result is False

    def test_should_include_asset_unknown_typename(self):
        """Test should_include_asset with unknown typename."""
        # Arrange
        asset_data = {"guid": "test_guid"}
        typename = "unknown_type"
        metadata_filter_state = "include"
        metadata_filter = {"app_1": []}

        # Act
        result = should_include_asset(
            asset_data, typename, metadata_filter_state, metadata_filter
        )

        # Assert
        assert result is True

    def test_should_include_asset_missing_app_guid(self):
        """Test should_include_asset with missing app GUID."""
        # Arrange
        asset_data = {}  # Missing guid field
        typename = "app"
        metadata_filter_state = "include"
        metadata_filter = {"app_1": []}

        # Act
        result = should_include_asset(
            asset_data, typename, metadata_filter_state, metadata_filter
        )

        # Assert
        assert result is False

    def test_should_include_asset_missing_page_fields(self):
        """Test should_include_asset with missing page fields."""
        # Arrange
        asset_data = {"guid": "page_1"}  # Missing appGuid
        typename = "page"
        metadata_filter_state = "include"
        metadata_filter = {"app_1": ["page_1"]}

        # Act
        result = should_include_asset(
            asset_data, typename, metadata_filter_state, metadata_filter
        )

        # Assert
        assert result is False

    def test_should_include_asset_exception_handling(self):
        """Test should_include_asset with exception handling."""
        # Arrange
        asset_data = {"guid": "test_guid"}
        typename = "app"
        metadata_filter_state = "include"
        metadata_filter = {"app_1": []}

        # Mock logger to avoid actual logging during test
        with patch("app.utils.logger"):
            # Act
            result = should_include_asset(
                asset_data, typename, metadata_filter_state, metadata_filter
            )

            # Assert
            # The function should return False because "test_guid" is not in the filter
            # and the filter state is "include"
            assert result is False
