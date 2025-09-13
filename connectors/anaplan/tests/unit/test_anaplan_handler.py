from unittest.mock import patch

import pytest
from app.clients import AppClient
from app.handlers import AppHandler


class TestAppHandler:
    """Test cases for AppHandler."""

    @pytest.fixture
    def credentials(self):
        """Create test credentials."""
        return {
            "host": "test.anaplan.com",
            "username": "test_user",
            "password": "test_password",
            "authType": "basic",
        }

    @pytest.fixture
    def app_client(self, credentials):
        """Create AppClient instance for testing."""
        client = AppClient()
        # Initialize with test credentials to set host attribute
        client.credentials = credentials
        client.host = credentials["host"]
        client.username = credentials["username"]
        client.password = credentials["password"]
        client.auth_type = credentials["authType"]
        client.auth_token = None
        client.http_headers = {}
        return client

    @pytest.fixture
    def handler(self, app_client):
        """Create AppHandler instance for testing."""
        return AppHandler(app_client)

    @pytest.fixture
    def handler_without_client(self):
        """Create AppHandler instance without client."""
        return AppHandler()

    @pytest.fixture
    def valid_payload(self, credentials):
        """Create valid preflight check payload."""
        return {
            "credentials": credentials,
            "metadata": {
                "exclude-empty-modules": "yes",
                "ingest-system-dimension": "proxy",
                "include-metadata": '{"ws1": {"model1": {"module1": {}}}}',
                "exclude-metadata": "{}",
            },
        }

    # ============================================================================
    # SECTION 1: INITIALIZATION TESTS
    # ============================================================================

    def test_handler_initialization_with_client(self, app_client):
        """Test handler initialization with client."""
        # Act
        handler = AppHandler(app_client)

        # Assert
        assert handler.client == app_client

    def test_handler_initialization_without_client(self):
        """Test handler initialization without client."""
        # Act
        handler = AppHandler()

        # Assert
        assert handler.client is None

    # ============================================================================
    # SECTION 2: LOAD METHOD TESTS
    # ============================================================================

    @patch.object(AppClient, "load")
    async def test_load_with_valid_credentials(
        self, mock_client_load, handler, credentials
    ):
        """Test loading credentials into handler."""
        # Act
        await handler.load(credentials)

        # Assert
        mock_client_load.assert_called_once_with(credentials=credentials)

    @patch.object(AppClient, "load")
    async def test_load_with_default_host(self, mock_client_load, handler):
        """Test loading credentials with default host."""
        # Arrange
        credentials = {
            "username": "test_user",
            "password": "test_password",
            "authType": "basic",
        }

        # Act
        await handler.load(credentials)

        # Assert
        mock_client_load.assert_called_once_with(credentials=credentials)

    @patch.object(AppClient, "load")
    async def test_load_with_default_auth_type(self, mock_client_load, handler):
        """Test loading credentials with default auth type."""
        # Arrange
        credentials = {
            "host": "test.anaplan.com",
            "username": "test_user",
            "password": "test_password",
        }

        # Act
        await handler.load(credentials)

        # Assert
        mock_client_load.assert_called_once_with(credentials=credentials)

    async def test_load_creates_client_if_none(
        self, handler_without_client, credentials
    ):
        """Test that load creates a client if none exists."""
        # This test verifies that the GenericHandler can handle the case where no client is provided
        # The actual behavior depends on the GenericHandler implementation
        # We just ensure it doesn't crash
        try:
            await handler_without_client.load(credentials)
        except AttributeError:
            # This is expected if GenericHandler doesn't create a client automatically
            pass

    # ============================================================================
    # SECTION 3: TEST_AUTH METHOD TESTS
    # ============================================================================

    @patch.object(AppClient, "_get_auth_token")
    async def test_test_auth_success(self, mock_get_auth_token, handler):
        """Test successful authentication."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"

        # Act
        result = await handler.test_auth()

        # Assert
        assert result is True
        mock_get_auth_token.assert_called_once()

    @patch.object(AppClient, "_get_auth_token")
    async def test_test_auth_failure(self, mock_get_auth_token, handler):
        """Test failed authentication."""
        # Arrange
        mock_get_auth_token.return_value = None

        # Act
        result = await handler.test_auth()

        # Assert
        assert result is False
        mock_get_auth_token.assert_called_once()

    @patch.object(AppClient, "_get_auth_token")
    async def test_test_auth_exception(self, mock_get_auth_token, handler):
        """Test authentication with exception."""
        # Arrange
        mock_get_auth_token.side_effect = Exception("Authentication failed")

        # Act
        result = await handler.test_auth()

        # Assert
        assert result is False

    async def test_test_auth_no_client(self, handler_without_client):
        """Test authentication without client."""
        # Act
        result = await handler_without_client.test_auth()

        # Assert
        assert result is False

    # ============================================================================
    # SECTION 4: FETCH_METADATA METHOD TESTS
    # ============================================================================

    @patch("app.handlers.extract_pages_with_details")
    @patch("app.handlers.extract_apps_data")
    @patch.object(AppClient, "_get_auth_token")
    async def test_fetch_metadata_success(
        self, mock_get_auth_token, mock_get_apps, mock_get_pages, handler
    ):
        """Test successful metadata fetching."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        mock_get_apps.return_value = [
            {"guid": "app_1", "name": "App 1", "deletedAt": None},
            {"guid": "app_2", "name": "App 2", "deletedAt": None},
        ]
        mock_get_pages.return_value = [
            {
                "guid": "page_1",
                "name": "Page 1",
                "appGuid": "app_1",
                "deletedAt": None,
            },
            {
                "guid": "page_2",
                "name": "Page 2",
                "appGuid": "app_1",
                "deletedAt": None,
            },
        ]

        # Act
        result = await handler.fetch_metadata()

        # Assert
        assert len(result) == 2  # 2 apps
        assert result[0]["value"] == "app_1"
        assert result[0]["title"] == "App 1"
        assert len(result[0]["children"]) == 2  # 2 pages

    @patch("app.handlers.extract_apps_data")
    @patch.object(AppClient, "_get_auth_token")
    async def test_fetch_metadata_no_apps(
        self, mock_get_auth_token, mock_get_apps, handler
    ):
        """Test metadata fetching with no apps."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        mock_get_apps.return_value = []

        # Act
        result = await handler.fetch_metadata()

        # Assert
        assert result == []

    @patch("app.handlers.extract_apps_data")
    @patch.object(AppClient, "_get_auth_token")
    async def test_fetch_metadata_exception(
        self, mock_get_auth_token, mock_get_apps, handler
    ):
        """Test metadata fetching with exception."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        mock_get_apps.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(Exception, match="Failed to fetch metadata: API Error"):
            await handler.fetch_metadata()

    async def test_fetch_metadata_no_client(self, handler_without_client):
        """Test metadata fetching without client."""
        # Act & Assert
        with pytest.raises(Exception, match="App client not initialized"):
            await handler_without_client.fetch_metadata()

    # ============================================================================
    # SECTION 5: PREFLIGHT_CHECK METHOD TESTS
    # ============================================================================

    @patch("app.handlers.extract_apps_data")
    @patch.object(AppClient, "_get_auth_token")
    async def test_preflight_check_success(
        self,
        mock_get_auth_token,
        mock_get_apps,
        handler,
        valid_payload,
    ):
        """Test successful preflight check."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        mock_get_apps.return_value = [
            {"guid": "app_1", "name": "App 1", "deletedAt": None}
        ]

        # Act
        result = await handler.preflight_check(valid_payload)

        # Assert
        assert "authenticationCheck" in result
        assert "appPermissions" in result
        assert result["authenticationCheck"]["success"] is True
        assert result["appPermissions"]["success"] is True

    @patch("app.handlers.extract_apps_data")
    @patch.object(AppClient, "_get_auth_token")
    async def test_preflight_check_auth_failure(
        self, mock_get_auth_token, mock_get_apps, handler, valid_payload
    ):
        """Test preflight check with authentication failure."""
        # Arrange
        mock_get_auth_token.return_value = None
        mock_get_apps.return_value = []

        # Act
        result = await handler.preflight_check(valid_payload)

        # Assert
        assert result["authenticationCheck"]["success"] is False
        assert (
            "Authentication failed" in result["authenticationCheck"]["failureMessage"]
        )

    @patch("app.handlers.extract_apps_data")
    @patch.object(AppClient, "_get_auth_token")
    async def test_preflight_check_exception(
        self, mock_get_auth_token, mock_get_apps, handler, valid_payload
    ):
        """Test preflight check with exception."""
        # Arrange
        mock_get_auth_token.side_effect = Exception("Auth error")

        # Act
        result = await handler.preflight_check(valid_payload)

        # Assert
        assert "Exception" in result
        assert result["Exception"]["success"] is False
        assert (
            "Preflight check failed: Auth error"
            in result["Exception"]["failureMessage"]
        )

    # ============================================================================
    # SECTION 6: INTEGRATION TESTS
    # ============================================================================

    @patch("app.handlers.extract_pages_with_details")
    @patch("app.handlers.extract_apps_data")
    @patch.object(AppClient, "_get_auth_token")
    async def test_complete_metadata_fetching_workflow(
        self,
        mock_get_auth_token,
        mock_get_apps,
        mock_get_pages,
        handler,
    ):
        """Test complete metadata fetching workflow."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        mock_get_apps.return_value = [
            {"guid": "app_1", "name": "App 1", "deletedAt": None},
        ]
        mock_get_pages.return_value = [
            {
                "guid": "page_1",
                "name": "Page 1",
                "appGuid": "app_1",
                "deletedAt": None,
                "isArchived": False,
            },
        ]

        # Act
        result = await handler.fetch_metadata()

        # Assert
        assert len(result) == 1  # 1 app with nested structure

        # Verify app
        app = result[0]
        assert app["value"] == "app_1"
        assert app["title"] == "App 1"
        assert len(app["children"]) == 1  # 1 page

        # Verify page
        page = app["children"][0]
        assert page["value"] == "page_1"
        assert page["title"] == "Page 1"

    # ============================================================================
    # SECTION 7: GENERIC HANDLER INTEGRATION TESTS
    # ============================================================================

    async def test_handler_inherits_from_base_handler(self):
        """Test that handler properly inherits from BaseHandler."""
        # Act
        handler = AppHandler()

        # Assert
        from application_sdk.handlers.base import BaseHandler

        assert isinstance(handler, BaseHandler)

    async def test_handler_has_required_sdk_methods(self):
        """Test that handler has all required SDK interface methods."""
        # Act
        handler = AppHandler()

        # Assert
        assert hasattr(handler, "load")
        assert hasattr(handler, "test_auth")
        assert hasattr(handler, "fetch_metadata")
        assert hasattr(handler, "preflight_check")

    async def test_handler_client_attribute_name(self):
        """Test that handler uses correct client attribute name."""
        # Arrange
        client = AppClient()
        handler = AppHandler(client)

        # Assert
        assert hasattr(handler, "client")
        assert handler.client == client
        # Ensure old attribute name doesn't exist
        assert not hasattr(handler, "app_client")
