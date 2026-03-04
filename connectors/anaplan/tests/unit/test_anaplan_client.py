from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from app.clients import AppClient
from application_sdk.common.error_codes import ClientError
from pydantic import ValidationError


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
    def ca_cert_credentials(self):
        """Create CA cert test credentials."""
        return {
            "host": "test.anaplan.com",
            "username": "encoded_data_value",
            "password": "encoded_signed_data_value",
            "authType": "ca_cert",
            "extra": {"CaCertificate": {"key": "workflow_file_upload/abc123.pem"}},
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
        client.cert_path = None
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

    @patch("app.clients.download_file_from_upload_response", new_callable=AsyncMock)
    @patch("app.clients.parse_credentials_extra")
    @patch.object(AppClient, "execute_http_post_request")
    async def test_load_with_ca_cert_credentials(
        self,
        mock_execute_post,
        mock_parse_extra,
        mock_download_cert,
        ca_cert_credentials,
    ):
        """Test loading CA cert credentials into client."""
        # Arrange
        mock_parse_extra.return_value = {
            "CaCertificate": {"key": "workflow_file_upload/abc123.pem"}
        }
        mock_download_cert.return_value = "/tmp/ca_cert.pem"

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {"tokenValue": "ca_cert_token_456"}
        }
        mock_execute_post.return_value = mock_response

        client = AppClient()
        client.http_headers = {}

        with patch("builtins.open", mock_open(read_data=b"cert_content")):
            await client.load(credentials=ca_cert_credentials)

        # Assert
        assert client.host == "test.anaplan.com"
        assert client.username == "encoded_data_value"
        assert client.password == "encoded_signed_data_value"
        assert client.auth_type == "ca_cert"
        assert client.cert_path == "/tmp/ca_cert.pem"
        assert client.auth_token == "ca_cert_token_456"
        mock_download_cert.assert_called_once()

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
        with pytest.raises(ValidationError):
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
        with pytest.raises(ClientError, match="Authentication failed with status 401"):
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
            ClientError,
            match="Username and password are required for basic authentication",
        ):
            await client._get_auth_token()

    async def test_get_auth_token_unsupported_auth_type(self, client):
        """Test authentication with unsupported auth type."""
        # Arrange
        client.auth_type = "oauth"

        # Act & Assert
        with pytest.raises(ClientError, match="Unsupported authentication type: oauth"):
            await client._get_auth_token()

    @patch.object(AppClient, "execute_http_post_request")
    async def test_get_auth_token_ca_cert_success(self, mock_execute_post, client):
        """Test successful CA cert authentication token retrieval."""
        # Arrange
        client.auth_type = "ca_cert"
        client.username = "encoded_data_value"
        client.password = "encoded_signed_data_value"
        client.cert_path = "/tmp/ca_cert.pem"

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {"tokenValue": "ca_cert_token_456"}
        }
        mock_execute_post.return_value = mock_response

        import base64

        cert_bytes = b"fake_cert_content"
        expected_b64 = base64.b64encode(cert_bytes).decode()

        # Act
        with patch("builtins.open", mock_open(read_data=cert_bytes)):
            result = await client._get_auth_token()

        # Assert
        assert result == "ca_cert_token_456"
        assert client.auth_token == "ca_cert_token_456"

        # Verify CACertificate header and JSON body
        mock_execute_post.assert_called_once()
        call_args = mock_execute_post.call_args
        assert call_args[0][0] == "https://auth.anaplan.com/token/authenticate"
        assert call_args[1]["headers"] == {
            "Authorization": f"CACertificate {expected_b64}"
        }
        assert call_args[1]["json_data"] == {
            "encodedData": "encoded_data_value",
            "encodedSignedData": "encoded_signed_data_value",
        }

    async def test_get_auth_token_ca_cert_missing_certificate(self, client):
        """Test CA cert authentication raises when cert_path is missing."""
        # Arrange
        client.auth_type = "ca_cert"
        client.cert_path = None

        # Act & Assert
        with pytest.raises(
            ClientError,
            match="CA Certificate is required for ca_cert authentication",
        ):
            await client._get_auth_token()

    def test_update_client_headers_with_token(self, client):
        """Test updating client headers with auth token (sync method)."""
        # Arrange
        client.auth_token = "test_token_123"

        # Act
        client._update_client_headers()

        # Assert
        assert client.http_headers == {
            "Authorization": "AnaplanAuthToken test_token_123",
            "Content-Type": "application/json",
        }

    def test_update_client_headers_without_token(self, client):
        """Test updating client headers without auth token (sync method)."""
        # Arrange
        client.auth_token = None

        # Act
        client._update_client_headers()

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
        with pytest.raises(ValidationError):
            await client.load(credentials=credentials)
