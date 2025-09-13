from unittest.mock import MagicMock, patch

import pytest
from app.clients import AppClient


class TestAppClient:
    """Test cases for AppClient."""

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
    def client(self, credentials):
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

    def test_init_with_defaults(self):
        """Test client initialization with default values."""
        # Act
        client = AppClient()

        # Assert - BaseClient may set some default attributes
        # We just verify that the client can be created without errors
        assert client is not None
        assert isinstance(client, AppClient)

    @patch.object(AppClient, "execute_http_post_request")
    async def test_load_with_valid_credentials(
        self, mock_execute_post, client, credentials
    ):
        """Test loading credentials into client."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                "tokenValue": "test_token_123",
            }
        }
        mock_execute_post.return_value = mock_response

        # Act
        await client.load(credentials=credentials)

        # Assert
        assert client.credentials == credentials
        assert client.host == "test.anaplan.com"
        assert client.username == "test_user"
        assert client.password == "test_password"
        assert client.auth_type == "basic"
        assert client.auth_token == "test_token_123"

        # Verify the API call
        mock_execute_post.assert_called_once()
        call_args = mock_execute_post.call_args
        assert call_args[0][0] == "https://auth.anaplan.com/token/authenticate"
        assert call_args[1]["auth"] == ("test_user", "test_password")

    @patch.object(AppClient, "execute_http_post_request")
    async def test_load_with_default_host(self, mock_execute_post, client):
        """Test loading credentials with default host."""
        # Arrange
        credentials = {
            "username": "test_user",
            "password": "test_password",
            "authType": "basic",
        }
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                "tokenValue": "test_token_123",
            }
        }
        mock_execute_post.return_value = mock_response

        # Act
        await client.load(credentials=credentials)

        # Assert
        assert client.host == "us1a.app.anaplan.com"  # Default host

    @patch.object(AppClient, "execute_http_post_request")
    async def test_load_with_default_auth_type(self, mock_execute_post, client):
        """Test loading credentials with default auth type."""
        # Arrange
        credentials = {
            "host": "test.anaplan.com",
            "username": "test_user",
            "password": "test_password",
        }
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                "tokenValue": "test_token_123",
            }
        }
        mock_execute_post.return_value = mock_response

        # Act
        await client.load(credentials=credentials)

        # Assert
        assert client.auth_type == "basic"  # Default auth type

    @patch.object(AppClient, "execute_http_post_request")
    async def test_get_auth_token_success(self, mock_execute_post, client, credentials):
        """Test successful authentication token retrieval."""
        # Arrange
        client.username = "test_user"
        client.password = "test_password"
        client.auth_type = "basic"

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                "tokenValue": "test_token_123",
            }
        }
        mock_execute_post.return_value = mock_response

        # Act
        result = await client._get_auth_token()

        # Assert
        assert result == "test_token_123"
        assert client.auth_token == "test_token_123"

        # Verify the API call
        mock_execute_post.assert_called_once()
        call_args = mock_execute_post.call_args
        assert call_args[0][0] == "https://auth.anaplan.com/token/authenticate"
        assert call_args[1]["auth"] == ("test_user", "test_password")

    @patch.object(AppClient, "execute_http_post_request")
    async def test_get_auth_token_missing_token(
        self, mock_execute_post, client, credentials
    ):
        """Test authentication when token is missing from response."""
        # Arrange
        client.username = "test_user"
        client.password = "test_password"
        client.auth_type = "basic"

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                # Missing tokenValue
            }
        }
        mock_execute_post.return_value = mock_response

        # Act & Assert
        with pytest.raises(
            Exception, match="Token not found in authentication response"
        ):
            await client._get_auth_token()

    @patch.object(AppClient, "execute_http_post_request")
    async def test_get_auth_token_authentication_failure(
        self, mock_execute_post, client, credentials
    ):
        """Test authentication failure."""
        # Arrange
        client.username = "test_user"
        client.password = "test_password"
        client.auth_type = "basic"

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.text = "Invalid credentials"
        mock_execute_post.return_value = mock_response

        # Act & Assert
        with pytest.raises(Exception, match="Authentication failed with status 401"):
            await client._get_auth_token()

    async def test_get_auth_token_missing_credentials(self):
        """Test authentication with missing username/password."""
        # Arrange
        client = AppClient()
        client.auth_type = "basic"
        client.username = None
        client.password = None

        # Act & Assert
        with pytest.raises(
            Exception,
            match="Username and password are required for basic authentication",
        ):
            await client._get_auth_token()

    async def test_get_auth_token_unsupported_auth_type(self, client):
        """Test authentication with unsupported auth type."""
        # Arrange
        client.auth_type = "oauth"

        # Act & Assert
        with pytest.raises(Exception, match="Unsupported authentication type: oauth"):
            await client._get_auth_token()

    async def test_update_client_headers_with_token(self, client):
        """Test updating client headers with auth token."""
        # Arrange
        client.auth_token = "test_token_123"

        # Act
        await client._update_client_headers()

        # Assert
        assert client.http_headers == {
            "Authorization": "AnaplanAuthToken test_token_123",
            "Content-Type": "application/json",
        }

    async def test_update_client_headers_without_token(self, client):
        """Test updating client headers without auth token."""
        # Arrange
        client.auth_token = None

        # Act
        await client._update_client_headers()

        # Assert
        assert client.http_headers == {"Content-Type": "application/json"}

    @patch.object(AppClient, "execute_http_post_request")
    async def test_load_network_error(self, mock_execute_post, client, credentials):
        """Test loading with network error."""
        # Arrange
        mock_execute_post.side_effect = Exception("Network error")

        # Act & Assert
        with pytest.raises(Exception, match="Network error"):
            await client.load(credentials=credentials)

    @patch.object(AppClient, "execute_http_post_request")
    async def test_load_invalid_response_format(
        self, mock_execute_post, client, credentials
    ):
        """Test loading with invalid response format."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            # Missing tokenInfo
            "status": "SUCCESS"
        }
        mock_execute_post.return_value = mock_response

        # Act & Assert
        with pytest.raises(
            Exception, match="Token not found in authentication response"
        ):
            await client.load(credentials=credentials)
