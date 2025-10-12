from unittest.mock import AsyncMock, MagicMock

import pytest
from app.extracts.apps import extract_apps_data


class TestAppsExtract:
    """Test cases for apps extraction functionality."""

    @pytest.fixture
    def mock_client(self):
        """Mock Anaplan API client."""
        client = MagicMock()
        client.execute_http_get_request = AsyncMock()
        client.host = "us1a.app.anaplan.com"
        client.auth_token = "test_token"
        return client

    async def test_extract_apps_data_success(self, mock_client):
        """Test successful apps extraction with specific scenario."""
        # Arrange - Minimal inline test data for specific scenario
        sample_response = {
            "items": [
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
            ],
            "paging": {
                "offset": 0,
                "limit": 100,
                "totalItemCount": 2,
            },
            "customerId": "test_customer_123",
        }

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = sample_response
        mock_client.execute_http_get_request.return_value = mock_response

        # Act
        result = await extract_apps_data(mock_client)

        # Assert
        assert len(result) == 2
        assert result[0]["guid"] == "app_guid_1"
        assert result[0]["name"] == "Test App 1"
        assert result[0]["customerId"] == "test_customer_123"
        assert result[0]["deletedAt"] is None
        assert result[0]["mpCount"] == 5
        assert result[0]["isFavorite"] is True

        assert result[1]["guid"] == "app_guid_2"
        assert result[1]["name"] == "Test App 2"
        assert result[1]["customerId"] == "test_customer_123"
        assert result[1]["deletedAt"] is None
        assert result[1]["mpCount"] == 3
        assert result[1]["isFavorite"] is False

        # Verify API call was made with correct parameters
        mock_client.execute_http_get_request.assert_called_once()
        call_args = mock_client.execute_http_get_request.call_args
        assert "springboard-definition-service/apps" in call_args[0][0]
        assert call_args[1]["params"] == {"limit": 100, "offset": 0}

    async def test_extract_apps_data_filters_deleted_apps(self, mock_client):
        """Test specific business logic: deleted apps should be filtered out."""
        # Arrange - Hardcoded scenario with deleted apps
        sample_response = {
            "items": [
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
            ],
            "paging": {
                "offset": 0,
                "limit": 100,
                "totalItemCount": 2,
            },
            "customerId": "test_customer_123",
        }

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = sample_response
        mock_client.execute_http_get_request.return_value = mock_response

        # Act
        result = await extract_apps_data(mock_client)

        # Assert
        assert len(result) == 1  # Only non-deleted app should be returned
        assert result[0]["guid"] == "app_guid_1"
        assert result[0]["name"] == "Active App"
        assert result[0]["deletedAt"] is None

        # Verify deleted app is not in result
        deleted_app_guids = [app["guid"] for app in result]
        assert "app_guid_2" not in deleted_app_guids

    async def test_extract_apps_data_pagination(self, mock_client):
        """Test specific scenario: pagination logic."""
        # Arrange - Hardcoded pagination scenario
        first_response = {
            "items": [
                {
                    "guid": "app_guid_1",
                    "name": "Test App 1",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                },
                {
                    "guid": "app_guid_2",
                    "name": "Test App 2",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                },
            ],
            "paging": {
                "offset": 0,
                "limit": 100,
                "totalItemCount": 150,  # More than limit to trigger pagination
            },
            "customerId": "test_customer_123",
        }

        second_response = {
            "items": [
                {
                    "guid": "app_guid_3",
                    "name": "Test App 3",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                }
            ],
            "paging": {
                "offset": 100,
                "limit": 100,
                "totalItemCount": 150,
            },
            "customerId": "test_customer_123",
        }

        mock_response_1 = MagicMock()
        mock_response_1.is_success = True
        mock_response_1.json.return_value = first_response

        mock_response_2 = MagicMock()
        mock_response_2.is_success = True
        mock_response_2.json.return_value = second_response

        mock_client.execute_http_get_request.side_effect = [
            mock_response_1,
            mock_response_2,
        ]

        # Act
        result = await extract_apps_data(mock_client)

        # Assert
        assert len(result) == 3  # Total from both pages
        assert result[0]["guid"] == "app_guid_1"
        assert result[1]["guid"] == "app_guid_2"
        assert result[2]["guid"] == "app_guid_3"

        # Verify both API calls were made with correct pagination
        assert mock_client.execute_http_get_request.call_count == 2
        calls = mock_client.execute_http_get_request.call_args_list

        # First call
        assert calls[0][1]["params"] == {"limit": 100, "offset": 0}
        # Second call
        assert calls[1][1]["params"] == {"limit": 100, "offset": 100}

    async def test_extract_apps_data_empty_response(self, mock_client):
        """Test specific scenario: empty response."""
        # Arrange - Hardcoded empty response
        empty_response = {
            "items": [],
            "paging": {"offset": 0, "limit": 100, "totalItemCount": 0},
            "customerId": "test_customer_123",
        }
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = empty_response
        mock_client.execute_http_get_request.return_value = mock_response

        # Act
        result = await extract_apps_data(mock_client)

        # Assert
        assert len(result) == 0

    async def test_extract_apps_data_api_failure(self, mock_client):
        """Test specific error scenario: API failure."""
        # Arrange - Hardcoded error response
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_client.execute_http_get_request.return_value = mock_response

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to fetch apps: 500"):
            await extract_apps_data(mock_client)

    async def test_extract_apps_data_no_response(self, mock_client):
        """Test specific error scenario: no response received."""
        # Arrange
        mock_client.execute_http_get_request.return_value = None

        # Act & Assert
        with pytest.raises(
            ValueError, match="Failed to extract apps data: No response received"
        ):
            await extract_apps_data(mock_client)

    async def test_extract_apps_data_missing_items_field(self, mock_client):
        """Test specific edge case: missing items field."""
        # Arrange - Hardcoded incomplete response
        incomplete_response = {
            "paging": {"offset": 0, "limit": 100, "totalItemCount": 0},
            "customerId": "test_customer_123",
        }
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = incomplete_response
        mock_client.execute_http_get_request.return_value = mock_response

        # Act
        result = await extract_apps_data(mock_client)

        # Assert
        assert len(result) == 0

    async def test_extract_apps_data_missing_paging_field(self, mock_client):
        """Test specific edge case: missing paging field."""
        # Arrange - Hardcoded incomplete response
        incomplete_response = {
            "items": [
                {
                    "guid": "app_guid_1",
                    "name": "Test App",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                }
            ],
            "customerId": "test_customer_123",
        }
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = incomplete_response
        mock_client.execute_http_get_request.return_value = mock_response

        # Act
        result = await extract_apps_data(mock_client)

        # Assert
        assert len(result) == 1
        assert result[0]["guid"] == "app_guid_1"

    async def test_extract_apps_data_all_apps_deleted(self, mock_client):
        """Test specific scenario: all apps are deleted."""
        # Arrange - Hardcoded scenario with all deleted apps
        all_deleted_response = {
            "items": [
                {
                    "guid": "app_guid_1",
                    "name": "Deleted App 1",
                    "customerId": "test_customer_123",
                    "deletedAt": "2024-01-01T00:00:00Z",
                },
                {
                    "guid": "app_guid_2",
                    "name": "Deleted App 2",
                    "customerId": "test_customer_123",
                    "deletedAt": "2024-01-02T00:00:00Z",
                },
            ],
            "paging": {"offset": 0, "limit": 100, "totalItemCount": 2},
            "customerId": "test_customer_123",
        }
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = all_deleted_response
        mock_client.execute_http_get_request.return_value = mock_response

        # Act
        result = await extract_apps_data(mock_client)

        # Assert
        assert len(result) == 0  # All apps filtered out as deleted

    async def test_extract_apps_data_exception_handling(self, mock_client):
        """Test specific error scenario: exception handling."""
        # Arrange
        mock_client.execute_http_get_request.side_effect = Exception("Network error")

        # Act & Assert
        with pytest.raises(Exception, match="Network error"):
            await extract_apps_data(mock_client)
