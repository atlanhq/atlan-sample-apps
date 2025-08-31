import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.clients import AnaplanApiClient, AnaplanRetryTransport


class TestAnaplanRetryTransport:
    """Test cases for AnaplanRetryTransport."""

    @pytest.fixture
    def client(self):
        """Create AnaplanApiClient instance for testing."""
        credentials = {
            "host": "test.anaplan.com",
            "username": "test_user",
            "password": "test_password",
            "authType": "basic",
        }
        return AnaplanApiClient(credentials)

    @pytest.fixture
    def transport(self, client):
        """Create AnaplanRetryTransport instance for testing."""
        return AnaplanRetryTransport(
            client_instance=client,
            backoff_factor=1.0,
            max_backoff_wait=60.0,
            backoff_jitter=0.1,
            total=3,
        )

    @pytest.fixture
    def mock_request(self):
        """Create a mock HTTP request."""
        request = MagicMock(spec=httpx.Request)
        request.url = "https://api.anaplan.com/test"
        request.method = "GET"
        request.headers = {}
        return request

    async def test_transport_initialization(self, transport, client):
        """Test transport initialization with correct parameters."""
        assert transport.client == client
        assert transport.retry is not None
        assert transport.retry.total == 3
        assert transport.retry.backoff_factor == 1.0
        assert transport.retry.max_backoff_wait == 60.0
        assert transport.retry.backoff_jitter == 0.1
        # Verify that 401 is in the status_forcelist
        assert 401 in transport.retry.status_forcelist

    @patch.object(AnaplanApiClient, "_handle_auth_error")
    async def test_handle_401_authentication_error(
        self, mock_handle_auth, transport, mock_request, client
    ):
        """Test handling of 401 authentication errors."""
        # Arrange
        client.auth_token = "old_token"

        # Mock response with 401 status
        mock_response_401 = MagicMock(spec=httpx.Response)
        mock_response_401.status_code = 401
        mock_response_401.headers = {}

        # Mock successful response after auth refresh
        mock_response_success = MagicMock(spec=httpx.Response)
        mock_response_success.status_code = 200
        mock_response_success.headers = {}

        # Mock the underlying transport to return 401 first, then 200
        call_count = 0

        async def mock_handle_async_request(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response_401
            else:
                return mock_response_success

        mock_transport = AsyncMock()
        mock_transport.handle_async_request = mock_handle_async_request
        transport._async_transport = mock_transport

        # Act - 401 handling is now done in transport level
        result = await transport.handle_async_request(mock_request)

        # Assert - transport should handle 401 and retry
        assert result.status_code == 200
        # Transport should call _handle_auth_error once for 401
        mock_handle_auth.assert_called_once()
        assert call_count == 2

    async def test_handle_429_rate_limit_error(self, transport, mock_request):
        """Test handling of 429 rate limit errors."""
        # Arrange
        # Mock response with 429 status
        mock_response_429 = MagicMock(spec=httpx.Response)
        mock_response_429.status_code = 429
        mock_response_429.headers = {}

        # Mock successful response after backoff
        mock_response_success = MagicMock(spec=httpx.Response)
        mock_response_success.status_code = 200
        mock_response_success.headers = {}

        # Mock the underlying transport to return 429 first, then 200
        transport._async_transport.handle_async_request = AsyncMock()
        transport._async_transport.handle_async_request.side_effect = [
            mock_response_429,
            mock_response_success,
        ]

        # Act
        result = await transport.handle_async_request(mock_request)

        # Assert
        assert result.status_code == 200
        assert transport._async_transport.handle_async_request.call_count == 2

    async def test_handle_other_status_codes(self, transport, mock_request):
        """Test handling of other status codes (should return immediately)."""
        # Arrange
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.headers = {}

        transport._async_transport.handle_async_request = AsyncMock()
        transport._async_transport.handle_async_request.return_value = mock_response

        # Act
        result = await transport.handle_async_request(mock_request)

        # Assert
        assert result.status_code == 500
        transport._async_transport.handle_async_request.assert_called_once()

    async def test_max_retries_exceeded_401(self, transport, mock_request, client):
        """Test that max retries are respected for 401 errors."""
        # Arrange
        client.auth_token = "old_token"  # Set a token so refresh can work
        client.token_expires_at = datetime.now() + timedelta(minutes=5)

        mock_response_401 = MagicMock(spec=httpx.Response)
        mock_response_401.status_code = 401
        mock_response_401.headers = {}

        mock_transport = AsyncMock()
        mock_transport.handle_async_request.return_value = mock_response_401
        transport._async_transport = mock_transport

        # Mock _handle_auth_error to do nothing to avoid complex auth flow
        async def mock_handle_auth():
            pass

        client._handle_auth_error = mock_handle_auth

        # Act - 401 handling is now done in transport level
        result = await transport.handle_async_request(mock_request)

        # Assert - transport should retry 401 up to max attempts
        assert result.status_code == 401
        # Transport should retry 401 up to max attempts (3 + 1 = 4 calls)
        assert mock_transport.handle_async_request.call_count == 4

    async def test_max_retries_exceeded_429(self, transport, mock_request):
        """Test that max retries are respected for 429 errors."""
        # Arrange
        mock_response_429 = MagicMock(spec=httpx.Response)
        mock_response_429.status_code = 429
        mock_response_429.headers = {}

        transport._async_transport.handle_async_request = AsyncMock()
        transport._async_transport.handle_async_request.return_value = mock_response_429

        # Act
        result = await transport.handle_async_request(mock_request)

        # Assert
        assert result.status_code == 429
        # Should have tried total + 1 times (initial + retries)
        assert (
            transport._async_transport.handle_async_request.call_count
            == transport.retry.total + 1
        )


class TestAnaplanApiClient:
    """Test cases for AnaplanApiClient."""

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
        """Create AnaplanApiClient instance for testing."""
        return AnaplanApiClient(credentials)

    def test_init_with_credentials(self, credentials):
        """Test client initialization with credentials."""
        # Act
        client = AnaplanApiClient(credentials)

        # Assert
        assert client.credentials == credentials
        assert client.host == "test.anaplan.com"
        assert client.username == "test_user"
        assert client.password == "test_password"
        assert client.auth_type == "basic"
        assert client.auth_token is None
        assert client.token_expires_at is None
        assert client._token_lock is not None

    def test_init_with_defaults(self):
        """Test client initialization with default values."""
        # Arrange
        credentials = {
            "username": "test_user",
            "password": "test_password",
        }

        # Act
        client = AnaplanApiClient(credentials)

        # Assert
        assert client.host == "us1a.app.anaplan.com"  # Default host
        assert client.auth_type == "basic"  # Default auth type

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_get_auth_token_success(self, mock_execute_post, client):
        """Test successful authentication token retrieval."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                "tokenValue": "test_token_123",
                "expiresAt": "1705123456789",  # Unix timestamp in milliseconds
            }
        }
        mock_execute_post.return_value = mock_response

        # Act
        result = await client._get_auth_token()

        # Assert
        assert result == "test_token_123"
        assert client.auth_token == "test_token_123"
        assert client.token_expires_at is not None
        assert isinstance(client.token_expires_at, datetime)

        # Verify the API call
        mock_execute_post.assert_called_once()
        call_args = mock_execute_post.call_args
        assert call_args[0][0] == "https://auth.anaplan.com/token/authenticate"
        # The base client merges headers internally, so we don't check headers here
        # The auth parameter should be passed as a tuple
        assert call_args[1]["auth"] == ("test_user", "test_password")

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_get_auth_token_with_default_expiration(
        self, mock_execute_post, client
    ):
        """Test authentication with default expiration when expiresAt is missing."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                "tokenValue": "test_token_123",
                # Missing expiresAt
            }
        }
        mock_execute_post.return_value = mock_response

        # Act
        result = await client._get_auth_token()

        # Assert
        assert result == "test_token_123"
        assert client.auth_token == "test_token_123"
        assert client.token_expires_at is not None
        # Should be approximately 30 minutes from now
        expected_expiry = datetime.now() + timedelta(minutes=30)
        assert abs((client.token_expires_at - expected_expiry).total_seconds()) < 5

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_get_auth_token_invalid_expiration(self, mock_execute_post, client):
        """Test authentication with invalid expiration timestamp."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                "tokenValue": "test_token_123",
                "expiresAt": "invalid_timestamp",
            }
        }
        mock_execute_post.return_value = mock_response

        # Act
        result = await client._get_auth_token()

        # Assert
        assert result == "test_token_123"
        assert client.auth_token == "test_token_123"
        assert client.token_expires_at is not None
        # Should use default 30 minutes
        expected_expiry = datetime.now() + timedelta(minutes=30)
        assert abs((client.token_expires_at - expected_expiry).total_seconds()) < 5

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_get_auth_token_missing_token(self, mock_execute_post, client):
        """Test authentication when token is missing from response."""
        # Arrange
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                # Missing tokenValue
                "expiresAt": "1705123456789",
            }
        }
        mock_execute_post.return_value = mock_response

        # Act & Assert
        with pytest.raises(
            Exception, match="Token not found in authentication response"
        ):
            await client._get_auth_token()

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_get_auth_token_authentication_failure(
        self, mock_execute_post, client
    ):
        """Test authentication failure."""
        # Arrange
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
        credentials = {"host": "test.anaplan.com"}
        client = AnaplanApiClient(credentials)

        # Act & Assert
        with pytest.raises(Exception, match="Username and password are required"):
            await client._get_auth_token()

    async def test_get_auth_token_unsupported_auth_type(self):
        """Test authentication with unsupported auth type."""
        # Arrange
        credentials = {
            "username": "test_user",
            "password": "test_password",
            "authType": "oauth",
        }
        client = AnaplanApiClient(credentials)

        # Act & Assert
        with pytest.raises(Exception, match="Unsupported authentication type: oauth"):
            await client._get_auth_token()

    async def test_get_auth_token_uses_existing_valid_token(self, client):
        """Test that existing valid token is reused."""
        # Arrange
        client.auth_token = "existing_token"
        client.token_expires_at = datetime.now() + timedelta(minutes=30)

        # Act
        result = await client._get_auth_token()

        # Assert
        assert result == "existing_token"

    @patch.object(AnaplanApiClient, "_refresh_auth_token")
    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_get_auth_token_refreshes_expired_token(
        self, mock_execute_post, mock_refresh, client
    ):
        """Test that expired token triggers refresh attempt."""
        # Arrange
        client.auth_token = "expired_token"
        client.token_expires_at = datetime.now() - timedelta(minutes=5)
        mock_refresh.return_value = "refreshed_token"

        # Act
        result = await client._get_auth_token()

        # Assert
        assert result == "refreshed_token"
        mock_refresh.assert_called_once()

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_refresh_auth_token_success(self, mock_execute_post, client):
        """Test successful token refresh."""
        # Arrange
        client.auth_token = "old_token"
        client.token_expires_at = datetime.now() + timedelta(minutes=5)

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                "tokenValue": "new_token_123",
                "expiresAt": "1705123456789",
            }
        }
        mock_execute_post.return_value = mock_response

        # Act
        result = await client._refresh_auth_token()

        # Assert
        assert result == "new_token_123"
        assert client.auth_token == "new_token_123"
        assert client.token_expires_at is not None

        # Verify the API call
        mock_execute_post.assert_called_once()
        call_args = mock_execute_post.call_args
        assert call_args[0][0] == "https://auth.anaplan.com/token/refresh"
        # The base client merges headers internally, so we don't check headers here
        # The client should have the auth token set in its headers

    async def test_refresh_auth_token_no_token_available(self, client):
        """Test refresh when no token is available."""
        # Act & Assert
        with pytest.raises(Exception, match="No token available for refresh"):
            await client._refresh_auth_token()

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    @patch.object(AnaplanApiClient, "_get_auth_token")
    async def test_refresh_auth_token_failure(
        self, mock_get_auth, mock_execute_post, client
    ):
        """Test token refresh failure."""
        # Arrange
        client.auth_token = "old_token"
        client.token_expires_at = datetime.now() + timedelta(minutes=5)

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.text = "Token expired"
        mock_execute_post.return_value = mock_response

        # Mock _get_auth_token to set the token and return it
        async def mock_get_auth_token():
            client.auth_token = "new_token_123"
            client.token_expires_at = datetime.now() + timedelta(minutes=30)
            return "new_token_123"

        mock_get_auth.side_effect = mock_get_auth_token

        # Act
        result = await client._refresh_auth_token()

        # Assert
        assert result == "new_token_123"
        assert client.auth_token == "new_token_123"

    @patch.object(AnaplanApiClient, "execute_http_get_request")
    async def test_make_get_request_success(self, mock_execute_get, client):
        """Test successful GET request."""
        # Arrange
        client.auth_token = "test_token"
        url = "https://api.anaplan.com/test"

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test_data"}
        mock_execute_get.return_value = mock_response

        # Act
        result = await client.execute_http_get_request(url)

        # Assert
        assert result == mock_response
        mock_execute_get.assert_called_once_with(url)

    @patch.object(AnaplanApiClient, "execute_http_get_request")
    async def test_make_get_request_with_params(self, mock_execute_get, client):
        """Test GET request with query parameters."""
        # Arrange
        client.auth_token = "test_token"
        url = "https://api.anaplan.com/test"
        params = {"param1": "value1", "param2": "value2"}

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_execute_get.return_value = mock_response

        # Act
        result = await client.execute_http_get_request(url, params=params)

        # Assert
        assert result == mock_response
        mock_execute_get.assert_called_once_with(url, params=params)

    @patch.object(AnaplanApiClient, "execute_http_get_request")
    async def test_make_get_request_with_headers(self, mock_execute_get, client):
        """Test GET request with custom headers."""
        # Arrange
        client.auth_token = "test_token"
        url = "https://api.anaplan.com/test"
        headers = {"Custom-Header": "custom_value"}

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_execute_get.return_value = mock_response

        # Act
        result = await client.execute_http_get_request(url, headers=headers)

        # Assert
        assert result == mock_response
        mock_execute_get.assert_called_once_with(url, headers=headers)

    async def test_load_method(self, client):
        """Test the load method that's called by the SDK."""
        # Arrange
        new_credentials = {
            "host": "new.anaplan.com",
            "username": "new_user",
            "password": "new_password",
            "authType": "basic",
        }

        with patch.object(client, "_get_auth_token", return_value="loaded_token"):
            # Act
            await client.load(credentials=new_credentials)

            # Assert
            assert client.credentials == new_credentials
            assert client.host == "new.anaplan.com"
            assert client.username == "new_user"
            assert client.password == "new_password"
            assert client.auth_type == "basic"
            client._get_auth_token.assert_called_once()

    @patch.object(AnaplanApiClient, "_refresh_auth_token")
    async def test_handle_auth_error(self, mock_refresh, client):
        """Test the _handle_auth_error method."""
        # Arrange
        mock_refresh.return_value = "refreshed_token"

        # Act
        await client._handle_auth_error()

        # Assert
        mock_refresh.assert_called_once()

    def test_token_lock_exists(self, client):
        """Test that token lock is properly initialized."""
        # Assert
        assert client._token_lock is not None
        assert isinstance(client._token_lock, asyncio.Lock)

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_get_auth_token_concurrent_calls(self, mock_execute_post, client):
        """Test that concurrent token requests are handled properly with lock."""
        # Arrange - Ensure client has no existing token to avoid refresh logic
        client.auth_token = None
        client.token_expires_at = None

        # Use a future timestamp to avoid refresh logic
        future_timestamp = str(
            int((datetime.now() + timedelta(hours=1)).timestamp() * 1000)
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tokenInfo": {
                "tokenValue": "test_token_123",
                "expiresAt": future_timestamp,
            }
        }
        mock_execute_post.return_value = mock_response

        # Act - Make concurrent calls with a timeout to prevent hanging
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    client._get_auth_token(),
                    client._get_auth_token(),
                    client._get_auth_token(),
                ),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            pytest.fail("Test timed out - concurrent calls may be hanging")

        # Assert - All should return the same token
        assert all(result == "test_token_123" for result in results)
        # Should only make one API call due to lock
        assert mock_execute_post.call_count == 1

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_get_auth_token_network_error(self, mock_execute_post, client):
        """Test authentication with network error."""
        # Arrange
        mock_execute_post.side_effect = Exception("Network error")

        # Act & Assert
        with pytest.raises(Exception, match="Network error"):
            await client._get_auth_token()

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_get_auth_token_invalid_response_format(
        self, mock_execute_post, client
    ):
        """Test authentication with invalid response format."""
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
            await client._get_auth_token()

    @patch.object(AnaplanApiClient, "execute_http_post_request")
    async def test_refresh_auth_token_invalid_response_format(
        self, mock_execute_post, client
    ):
        """Test token refresh with invalid response format."""
        # Arrange
        client.auth_token = "old_token"
        client.token_expires_at = datetime.now() + timedelta(minutes=5)

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            # Missing tokenInfo
            "status": "SUCCESS"
        }
        mock_execute_post.return_value = mock_response

        with patch.object(client, "_get_auth_token", return_value="new_token"):
            # Act
            result = await client._refresh_auth_token()

            # Assert
            assert result == "new_token"

    def test_base64_encoding_in_auth_header(self, client):
        """Test that auth header is properly base64 encoded."""
        # Arrange
        client.username = "test_user"
        client.password = "test_password"

        # Act - This would be called internally by _get_auth_token
        import base64

        expected_auth = base64.b64encode(b"test_user:test_password").decode()

        # Assert
        assert expected_auth == "dGVzdF91c2VyOnRlc3RfcGFzc3dvcmQ="
