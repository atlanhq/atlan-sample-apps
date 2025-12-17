from unittest.mock import AsyncMock, MagicMock

import pytest
from app.extracts.pages import extract_pages_with_details


class TestPagesExtract:
    """Test cases for pages extraction functionality."""

    @pytest.fixture
    def mock_client(self):
        """Mock Anaplan API client."""
        client = MagicMock()
        client.execute_http_get_request = AsyncMock()
        client.host = "us1a.app.anaplan.com"
        client.auth_token = "test_token"
        return client

    async def test_extract_pages_with_details_success(self, mock_client):
        """Test successful pages extraction with specific scenario."""
        # Arrange - Minimal inline test data for specific scenario
        sample_response = {
            "items": [
                {
                    "guid": "page_guid_1",
                    "name": "Test Page 1",
                    "description": "Test Page Description 1",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                    "appGuid": "app_guid_1",
                    "isArchived": False,
                },
                {
                    "guid": "page_guid_2",
                    "name": "Test Page 2",
                    "description": "Test Page Description 2",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                    "appGuid": "app_guid_1",
                    "isArchived": True,
                },
            ]
        }

        # Create responses for pagination simulation
        first_response = MagicMock()
        first_response.is_success = True
        first_response.json.return_value = sample_response

        # Empty response to break the pagination loop
        empty_response = MagicMock()
        empty_response.is_success = True
        empty_response.json.return_value = {"items": []}

        # Use side_effect to return different responses for different calls
        mock_client.execute_http_get_request.side_effect = [
            first_response,
            empty_response,
        ]

        # Act
        all_apps = {"app_guid_1", "app_guid_2"}
        result = await extract_pages_with_details(mock_client, all_apps)

        # Assert
        assert len(result) == 1  # Only non-archived page should be returned
        assert result[0]["guid"] == "page_guid_1"
        assert result[0]["name"] == "Test Page 1"
        assert result[0]["customerId"] == "test_customer_123"
        assert result[0]["deletedAt"] is None
        assert result[0]["appGuid"] == "app_guid_1"
        assert result[0]["isArchived"] is False

        # Verify archived page is not in result
        page_guids = [page["guid"] for page in result]
        assert "page_guid_2" not in page_guids

        # Verify API calls were made with correct parameters
        assert mock_client.execute_http_get_request.call_count == 2
        calls = mock_client.execute_http_get_request.call_args_list

        # First call
        assert "springboard-definition-service/pages" in calls[0][0][0]
        assert calls[0][1]["params"] == {
            "limit": 100,
            "offset": 0,
            "sort": "lastAccessed",
            "order": "desc",
            "includeReportPages": True,
        }

        # Second call (pagination)
        assert "springboard-definition-service/pages" in calls[1][0][0]
        assert calls[1][1]["params"] == {
            "limit": 100,
            "offset": 100,
            "sort": "lastAccessed",
            "order": "desc",
            "includeReportPages": True,
        }

    async def test_extract_pages_filters_deleted_pages(self, mock_client):
        """Test specific business logic: deleted pages should be filtered out."""
        # Arrange - Hardcoded scenario with deleted pages
        sample_response = {
            "items": [
                {
                    "guid": "page_guid_1",
                    "name": "Active Page",
                    "description": "Active Page Description",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                    "appGuid": "app_guid_1",
                    "isArchived": False,
                },
                {
                    "guid": "page_guid_2",
                    "name": "Deleted Page",
                    "description": "Deleted Page Description",
                    "customerId": "test_customer_123",
                    "deletedAt": "2024-01-01T00:00:00Z",
                    "appGuid": "app_guid_1",
                    "isArchived": False,
                },
            ]
        }

        # Create responses for pagination simulation
        first_response = MagicMock()
        first_response.is_success = True
        first_response.json.return_value = sample_response

        # Empty response to break the pagination loop
        empty_response = MagicMock()
        empty_response.is_success = True
        empty_response.json.return_value = {"items": []}

        # Use side_effect to return different responses for different calls
        mock_client.execute_http_get_request.side_effect = [
            first_response,
            empty_response,
        ]

        # Act
        all_apps = {"app_guid_1"}
        result = await extract_pages_with_details(mock_client, all_apps)

        # Assert
        assert len(result) == 1  # Only non-deleted page should be returned
        assert result[0]["guid"] == "page_guid_1"
        assert result[0]["name"] == "Active Page"
        assert result[0]["deletedAt"] is None

        # Verify deleted page is not in result
        deleted_page_guids = [page["guid"] for page in result]
        assert "page_guid_2" not in deleted_page_guids

    async def test_extract_pages_filters_by_app_guids(self, mock_client):
        """Test specific business logic: pages should be filtered by valid app GUIDs."""
        # Arrange - Hardcoded scenario with pages from different apps
        sample_response = {
            "items": [
                {
                    "guid": "page_guid_1",
                    "name": "Page from Valid App",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                    "appGuid": "app_guid_1",  # Valid app
                },
                {
                    "guid": "page_guid_2",
                    "name": "Page from Invalid App",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                    "appGuid": "app_guid_999",  # Invalid app
                },
            ]
        }

        # Create responses for pagination simulation
        first_response = MagicMock()
        first_response.is_success = True
        first_response.json.return_value = sample_response

        # Empty response to break the pagination loop
        empty_response = MagicMock()
        empty_response.is_success = True
        empty_response.json.return_value = {"items": []}

        # Use side_effect to return different responses for different calls
        mock_client.execute_http_get_request.side_effect = [
            first_response,
            empty_response,
        ]

        # Act
        all_apps = {"app_guid_1"}  # Only app_guid_1 is valid
        result = await extract_pages_with_details(mock_client, all_apps)

        # Assert
        assert len(result) == 1  # Only page from valid app should be returned
        assert result[0]["guid"] == "page_guid_1"
        assert result[0]["appGuid"] == "app_guid_1"

        # Verify page from invalid app is not in result
        page_guids = [page["guid"] for page in result]
        assert "page_guid_2" not in page_guids

    async def test_extract_pages_empty_response(self, mock_client):
        """Test specific scenario: empty response."""
        # Arrange - Hardcoded empty response
        empty_response = {"items": []}
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = empty_response
        mock_client.execute_http_get_request.return_value = mock_response

        # Act
        all_apps = {"app_guid_1"}
        result = await extract_pages_with_details(mock_client, all_apps)

        # Assert
        assert len(result) == 0

    async def test_extract_pages_api_failure(self, mock_client):
        """Test specific error scenario: API failure."""
        # Arrange - Hardcoded error response
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_client.execute_http_get_request.return_value = mock_response

        # Act & Assert
        all_apps = {"app_guid_1"}
        with pytest.raises(ValueError, match="Failed to fetch pages: 500"):
            await extract_pages_with_details(mock_client, all_apps)

    async def test_extract_pages_no_response(self, mock_client):
        """Test specific error scenario: no response received."""
        # Arrange
        mock_client.execute_http_get_request.return_value = None

        # Act & Assert
        all_apps = {"app_guid_1"}
        with pytest.raises(
            ValueError, match="Failed to extract pages data: No response received"
        ):
            await extract_pages_with_details(mock_client, all_apps)

    async def test_extract_pages_missing_items_field(self, mock_client):
        """Test specific edge case: missing items field."""
        # Arrange - Hardcoded incomplete response
        incomplete_response = {}
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = incomplete_response
        mock_client.execute_http_get_request.return_value = mock_response

        # Act
        all_apps = {"app_guid_1"}
        result = await extract_pages_with_details(mock_client, all_apps)

        # Assert
        assert len(result) == 0

    async def test_extract_pages_missing_paging_field(self, mock_client):
        """Test specific edge case: missing paging field."""
        # Arrange - Hardcoded incomplete response
        incomplete_response = {
            "items": [
                {
                    "guid": "page_guid_1",
                    "name": "Test Page",
                    "customerId": "test_customer_123",
                    "deletedAt": None,
                    "appGuid": "app_guid_1",
                }
            ]
        }

        # Create responses for pagination simulation
        first_response = MagicMock()
        first_response.is_success = True
        first_response.json.return_value = incomplete_response

        # Empty response to break the pagination loop
        empty_response = MagicMock()
        empty_response.is_success = True
        empty_response.json.return_value = {"items": []}

        # Use side_effect to return different responses for different calls
        mock_client.execute_http_get_request.side_effect = [
            first_response,
            empty_response,
        ]

        # Act
        all_apps = {"app_guid_1"}
        result = await extract_pages_with_details(mock_client, all_apps)

        # Assert
        assert len(result) == 1
        assert result[0]["guid"] == "page_guid_1"

    async def test_extract_pages_all_pages_deleted(self, mock_client):
        """Test specific scenario: all pages are deleted."""
        # Arrange - Hardcoded scenario with all deleted pages
        all_deleted_response = {
            "items": [
                {
                    "guid": "page_guid_1",
                    "name": "Deleted Page 1",
                    "customerId": "test_customer_123",
                    "deletedAt": "2024-01-01T00:00:00Z",
                    "appGuid": "app_guid_1",
                },
                {
                    "guid": "page_guid_2",
                    "name": "Deleted Page 2",
                    "customerId": "test_customer_123",
                    "deletedAt": "2024-01-02T00:00:00Z",
                    "appGuid": "app_guid_1",
                },
            ]
        }

        # Create responses for pagination simulation
        first_response = MagicMock()
        first_response.is_success = True
        first_response.json.return_value = all_deleted_response

        # Empty response to break the pagination loop
        empty_response = MagicMock()
        empty_response.is_success = True
        empty_response.json.return_value = {"items": []}

        # Use side_effect to return different responses for different calls
        mock_client.execute_http_get_request.side_effect = [
            first_response,
            empty_response,
        ]

        # Act
        all_apps = {"app_guid_1"}
        result = await extract_pages_with_details(mock_client, all_apps)

        # Assert
        assert len(result) == 0  # All pages filtered out as deleted

    async def test_extract_pages_exception_handling(self, mock_client):
        """Test specific error scenario: exception handling."""
        # Arrange
        mock_client.execute_http_get_request.side_effect = Exception("Network error")

        # Act & Assert
        all_apps = {"app_guid_1"}
        with pytest.raises(Exception, match="Network error"):
            await extract_pages_with_details(mock_client, all_apps)
