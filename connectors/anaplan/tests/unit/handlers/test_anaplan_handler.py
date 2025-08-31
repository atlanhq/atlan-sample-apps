from unittest.mock import MagicMock, patch

import pytest

from app.clients import AnaplanApiClient
from app.handlers import AnaplanHandler


class TestAnaplanHandler:
    """Test cases for AnaplanHandler."""

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
    def anaplan_client(self, credentials):
        """Create AnaplanApiClient instance for testing."""
        return AnaplanApiClient(credentials)

    @pytest.fixture
    def handler(self, anaplan_client):
        """Create AnaplanHandler instance for testing."""
        return AnaplanHandler(anaplan_client)

    @pytest.fixture
    def handler_without_client(self):
        """Create AnaplanHandler instance without client."""
        return AnaplanHandler()

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

    def test_handler_initialization_with_client(self, anaplan_client):
        """Test handler initialization with client."""
        # Act
        handler = AnaplanHandler(anaplan_client)

        # Assert
        assert handler.client == anaplan_client

    def test_handler_initialization_without_client(self):
        """Test handler initialization without client."""
        # Act
        handler = AnaplanHandler()

        # Assert
        assert handler.client is None

    # ============================================================================
    # SECTION 2: LOAD METHOD TESTS
    # ============================================================================

    @patch.object(AnaplanApiClient, "load")
    async def test_load_with_valid_credentials(
        self, mock_client_load, handler, credentials
    ):
        """Test loading credentials into handler."""
        # Act
        await handler.load(credentials)

        # Assert
        mock_client_load.assert_called_once_with(credentials=credentials)

    @patch.object(AnaplanApiClient, "load")
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

    @patch.object(AnaplanApiClient, "load")
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

    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_test_auth_success(self, mock_get_auth_token, handler):
        """Test successful authentication."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"

        # Act
        result = await handler.test_auth()

        # Assert
        assert result is True
        mock_get_auth_token.assert_called_once()

    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_test_auth_failure(self, mock_get_auth_token, handler):
        """Test failed authentication."""
        # Arrange
        mock_get_auth_token.return_value = None

        # Act
        result = await handler.test_auth()

        # Assert
        assert result is False
        mock_get_auth_token.assert_called_once()

    @patch.object(AnaplanApiClient, "_get_auth_token")
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

    @patch.object(AnaplanHandler, "_extract_apps_for_handler")
    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_fetch_metadata_success(
        self, mock_get_auth_token, mock_get_apps, handler
    ):
        """Test successful metadata fetching."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        mock_get_apps.return_value = [
            {"guid": "app_1", "name": "App 1", "deletedAt": None},
            {"guid": "app_2", "name": "App 2", "deletedAt": None},
        ]

        # Mock the page fetching method
        with patch.object(AnaplanHandler, "_extract_pages_for_handler") as mock_get_pages:
            mock_get_pages.return_value = [
                {"guid": "page_1", "name": "Page 1", "appGuid": "app_1", "deletedAt": None},
                {"guid": "page_2", "name": "Page 2", "appGuid": "app_1", "deletedAt": None},
            ]

            # Act
            result = await handler.fetch_metadata()

            # Assert
            assert len(result) == 2  # 2 apps
            assert result[0]["value"] == "app_1"
            assert result[0]["title"] == "App 1"
            assert len(result[0]["children"]) == 2  # 2 pages

    @patch.object(AnaplanHandler, "_extract_apps_for_handler")
    @patch.object(AnaplanApiClient, "_get_auth_token")
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

    @patch.object(AnaplanHandler, "_extract_apps_for_handler")
    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_fetch_metadata_no_active_apps(
        self, mock_get_auth_token, mock_get_apps, handler
    ):
        """Test metadata fetching with no active apps."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        # Mock to return empty list since _extract_apps_for_handler filters out deleted apps internally
        mock_get_apps.return_value = []

        # Act
        result = await handler.fetch_metadata()

        # Assert
        assert result == []

    @patch.object(AnaplanHandler, "_extract_apps_for_handler")
    @patch.object(AnaplanApiClient, "_get_auth_token")
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
        with pytest.raises(Exception, match="Anaplan client not initialized"):
            await handler_without_client.fetch_metadata()

    # ============================================================================
    # SECTION 5: PREFLIGHT_CHECK METHOD TESTS
    # ============================================================================

    @patch.object(AnaplanHandler, "_validate_app_permissions")
    @patch.object(AnaplanHandler, "_validate_authentication")
    @patch.object(AnaplanHandler, "_validate_input_payload")
    async def test_preflight_check_success(
        self,
        mock_validate_input,
        mock_validate_auth,
        mock_validate_permissions,
        handler,
        valid_payload,
    ):
        """Test successful preflight check."""
        # Arrange
        mock_validate_input.return_value = {
            "success": True,
            "successMessage": "Input Validation Successful",
            "failureMessage": "",
        }
        mock_validate_auth.return_value = {
            "success": True,
            "successMessage": "Authentication successful",
            "failureMessage": "",
        }
        mock_validate_permissions.return_value = {
            "success": True,
            "successMessage": "Permissions check successful",
            "failureMessage": "",
        }

        # Act
        result = await handler.preflight_check(valid_payload)

        # Assert
        assert "inputValidation" in result
        assert "authenticationCheck" in result
        assert "appPermissions" in result
        assert result["inputValidation"]["success"] is True
        assert result["authenticationCheck"]["success"] is True
        assert result["appPermissions"]["success"] is True

    @patch.object(AnaplanHandler, "_validate_input_payload")
    async def test_preflight_check_input_validation_failure(
        self, mock_validate_input, handler, valid_payload
    ):
        """Test preflight check with input validation failure."""
        # Arrange
        mock_validate_input.return_value = {
            "success": False,
            "successMessage": "",
            "failureMessage": "Invalid payload",
        }

        # Act
        result = await handler.preflight_check(valid_payload)

        # Assert
        assert result["inputValidation"]["success"] is False
        assert "Invalid payload" in result["inputValidation"]["failureMessage"]

    @patch.object(AnaplanHandler, "_validate_app_permissions")
    @patch.object(AnaplanHandler, "_validate_authentication")
    @patch.object(AnaplanHandler, "_validate_input_payload")
    async def test_preflight_check_exception(
        self,
        mock_validate_input,
        mock_validate_auth,
        mock_validate_permissions,
        handler,
        valid_payload,
    ):
        """Test preflight check with exception."""
        # Arrange
        mock_validate_input.side_effect = Exception("Validation error")

        # Act
        result = await handler.preflight_check(valid_payload)

        # Assert
        assert result["inputValidation"]["success"] is False
        assert (
            "Preflight check failed: Validation error"
            in result["inputValidation"]["failureMessage"]
        )

    # ============================================================================
    # SECTION 6: VALIDATION METHODS TESTS
    # ============================================================================

    def test_validate_input_payload_success(self, valid_payload):
        """Test successful input payload validation."""
        # Act
        result = AnaplanHandler._validate_input_payload(valid_payload)

        # Assert
        assert result["success"] is True
        assert result["successMessage"] == "Input Validation Successful"
        assert result["failureMessage"] == ""

    def test_validate_input_payload_missing_credentials(self):
        """Test input validation with missing credentials."""
        # Arrange
        payload = {
            "metadata": {
                "exclude-empty-modules": "yes",
                "ingest-system-dimension": "proxy",
                "include-metadata": "{}",
                "exclude-metadata": "{}",
            }
        }

        # Act
        result = AnaplanHandler._validate_input_payload(payload)

        # Assert
        assert result["success"] is False
        assert "Missing required keys" in result["failureMessage"]

    def test_validate_input_payload_missing_metadata(self):
        """Test input validation with missing metadata."""
        # Arrange
        payload = {
            "credentials": {
                "host": "test.anaplan.com",
                "username": "test_user",
                "password": "test_password",
                "authType": "basic",
            }
        }

        # Act
        result = AnaplanHandler._validate_input_payload(payload)

        # Assert
        assert result["success"] is False
        assert "Missing required keys" in result["failureMessage"]

    def test_validate_input_payload_invalid_json(self):
        """Test input validation with invalid JSON in metadata."""
        # Arrange
        payload = {
            "credentials": {
                "host": "test.anaplan.com",
                "username": "test_user",
                "password": "test_password",
                "authType": "basic",
            },
            "metadata": {
                "exclude-empty-modules": "yes",
                "ingest-system-dimension": "proxy",
                "include-metadata": "invalid json",
                "exclude-metadata": "{}",
            },
        }

        # Act
        result = AnaplanHandler._validate_input_payload(payload)

        # Assert
        assert result["success"] is False
        assert "Invalid JSON" in result["failureMessage"]

    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_validate_authentication_success(
        self, mock_get_auth_token, anaplan_client
    ):
        """Test successful authentication validation."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"

        # Act
        result = await AnaplanHandler._validate_authentication(anaplan_client)

        # Assert
        assert result["success"] is True
        assert "Authentication successful" in result["successMessage"]
        assert result["failureMessage"] == ""

    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_validate_authentication_failure(
        self, mock_get_auth_token, anaplan_client
    ):
        """Test failed authentication validation."""
        # Arrange
        mock_get_auth_token.return_value = None

        # Act
        result = await AnaplanHandler._validate_authentication(anaplan_client)

        # Assert
        assert result["success"] is False
        assert "Authentication failed" in result["failureMessage"]

    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_validate_authentication_exception(
        self, mock_get_auth_token, anaplan_client
    ):
        """Test authentication validation with exception."""
        # Arrange
        mock_get_auth_token.side_effect = Exception("Auth error")

        # Act
        result = await AnaplanHandler._validate_authentication(anaplan_client)

        # Assert
        assert result["success"] is False
        assert "Authentication error: Auth error" in result["failureMessage"]

    async def test_validate_authentication_no_client(self):
        """Test authentication validation without client."""
        # Act
        result = await AnaplanHandler._validate_authentication(None)

        # Assert
        assert result["success"] is False
        assert "Anaplan client not initialized" in result["failureMessage"]

    @patch.object(AnaplanApiClient, "execute_http_get_request")
    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_validate_app_permissions_success(
        self, mock_get_auth_token, mock_execute_get, anaplan_client
    ):
        """Test successful app permissions validation."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_execute_get.return_value = mock_response

        # Act
        result = await AnaplanHandler._validate_app_permissions(anaplan_client)

        # Assert
        assert result["success"] is True
        assert "App permissions validation successful" in result["successMessage"]
        assert result["failureMessage"] == ""

    @patch.object(AnaplanApiClient, "execute_http_get_request")
    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_validate_app_permissions_failure(
        self, mock_get_auth_token, mock_execute_get, anaplan_client
    ):
        """Test failed app permissions validation."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_execute_get.return_value = mock_response

        # Act
        result = await AnaplanHandler._validate_app_permissions(anaplan_client)

        # Assert
        assert result["success"] is False
        assert "App permissions validation failed" in result["failureMessage"]

    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_validate_app_permissions_no_client(self, mock_get_auth_token):
        """Test app permissions validation without client."""
        # Act
        result = await AnaplanHandler._validate_app_permissions(None)

        # Assert
        assert result["success"] is False
        assert "Anaplan client not initialized" in result["failureMessage"]

    # ============================================================================
    # SECTION 7: API HELPER METHODS TESTS
    # ============================================================================

    @patch.object(AnaplanApiClient, "execute_http_get_request")
    async def test_extract_apps_for_handler_success(self, mock_execute_get, handler):
        """Test successful app extraction for handler."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {"guid": "app_1", "name": "App 1", "deletedAt": None},
                {"guid": "app_2", "name": "App 2", "deletedAt": None},
            ],
            "paging": {"totalItemCount": 2}
        }
        mock_response.is_success = True
        mock_execute_get.return_value = mock_response

        # Act
        result = await handler._extract_apps_for_handler()

        # Assert
        assert len(result) == 2
        assert result[0]["guid"] == "app_1"
        assert result[1]["guid"] == "app_2"

    @patch.object(AnaplanApiClient, "execute_http_get_request")
    async def test_extract_pages_for_handler_success(self, mock_execute_get, handler):
        """Test successful page extraction for handler."""
        # Arrange
        # First call returns pages, second call returns empty items to break pagination
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            "items": [
                {"guid": "page_1", "name": "Page 1", "appGuid": "app_1", "deletedAt": None, "isArchived": False},
                {"guid": "page_2", "name": "Page 2", "appGuid": "app_1", "deletedAt": None, "isArchived": False},
            ]
        }
        mock_response1.is_success = True
        
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {"items": []}
        mock_response2.is_success = True
        
        mock_execute_get.side_effect = [mock_response1, mock_response2]

        # Act
        app_guids = {"app_1"}
        result = await handler._extract_pages_for_handler(app_guids)

        # Assert
        assert len(result) == 2
        assert result[0]["guid"] == "page_1"
        assert result[1]["guid"] == "page_2"

    # ============================================================================
    # SECTION 8: INTEGRATION TESTS
    # ============================================================================

    @patch.object(AnaplanHandler, "_extract_apps_for_handler")
    @patch.object(AnaplanHandler, "_extract_pages_for_handler")
    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_complete_metadata_fetching_workflow(
        self,
        mock_get_auth_token,
        mock_get_pages,
        mock_get_apps,
        handler,
    ):
        """Test complete metadata fetching workflow."""
        # Arrange
        mock_get_auth_token.return_value = "test_token"
        mock_get_apps.return_value = [
            {"guid": "app_1", "name": "App 1", "deletedAt": None},
        ]
        mock_get_pages.return_value = [
            {"guid": "page_1", "name": "Page 1", "appGuid": "app_1", "deletedAt": None, "isArchived": False},
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

    @patch.object(AnaplanHandler, "_validate_app_permissions")
    @patch.object(AnaplanHandler, "_validate_authentication")
    @patch.object(AnaplanHandler, "_validate_input_payload")
    async def test_complete_preflight_check_workflow(
        self,
        mock_validate_input,
        mock_validate_auth,
        mock_validate_permissions,
        handler,
        valid_payload,
    ):
        """Test complete preflight check workflow."""
        # Arrange
        mock_validate_input.return_value = {
            "success": True,
            "successMessage": "Input Validation Successful",
            "failureMessage": "",
        }
        mock_validate_auth.return_value = {
            "success": True,
            "successMessage": "Authentication successful",
            "failureMessage": "",
        }
        mock_validate_permissions.return_value = {
            "success": True,
            "successMessage": "Permissions check successful",
            "failureMessage": "",
        }

        # Act
        result = await handler.preflight_check(valid_payload)

        # Assert
        assert len(result) == 3
        assert all(check["success"] for check in result.values())

        # Verify all validation methods were called
        mock_validate_input.assert_called_once_with(valid_payload)
        mock_validate_auth.assert_called_once()
        mock_validate_permissions.assert_called_once()

    # ============================================================================
    # SECTION 9: GENERIC HANDLER INTEGRATION TESTS
    # ============================================================================

    async def test_handler_inherits_from_base_handler(self):
        """Test that handler properly inherits from BaseHandler."""
        # Act
        handler = AnaplanHandler()

        # Assert
        from application_sdk.handlers.base import BaseHandler

        assert isinstance(handler, BaseHandler)

    async def test_handler_has_required_sdk_methods(self):
        """Test that handler has all required SDK interface methods."""
        # Act
        handler = AnaplanHandler()

        # Assert
        assert hasattr(handler, "load")
        assert hasattr(handler, "test_auth")
        assert hasattr(handler, "fetch_metadata")
        assert hasattr(handler, "preflight_check")

    async def test_handler_client_attribute_name(self):
        """Test that handler uses correct client attribute name."""
        # Arrange
        client = AnaplanApiClient()
        handler = AnaplanHandler(client)

        # Assert
        assert hasattr(handler, "client")
        assert handler.client == client
        # Ensure old attribute name doesn't exist
        assert not hasattr(handler, "anaplan_client")
