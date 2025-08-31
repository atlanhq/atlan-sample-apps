import asyncio
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Any, Callable, Coroutine, Dict, Optional, Union

import httpx
from application_sdk.clients.base import BaseClient
from application_sdk.observability.logger_adaptor import get_logger
from httpx_retries import Retry, RetryTransport

logger = get_logger(__name__)


class AnaplanRetryTransport(RetryTransport):
    """
    Custom transport for Anaplan API that extends RetryTransport of httpx-retries to handle 401 authentication.

    This transport uses the standard RetryTransport functionality for 429 and other errors,
    but adds custom handling for 401 authentication errors.
    """

    def __init__(self, client_instance: "AnaplanApiClient", **retry_kwargs):
        """
        Initialize the Anaplan retry transport.

        Args:
            client_instance: The AnaplanApiClient instance
            **retry_kwargs: Arguments passed to Retry
        """
        # Only retry for 429 (rate limiting) and 401 (authentication) for Anaplan
        status_forcelist = retry_kwargs.get(
            "status_forcelist", [HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.UNAUTHORIZED]
        )
        retry_kwargs["status_forcelist"] = status_forcelist

        # Create retry configuration using the base Retry class
        retry = Retry(**retry_kwargs)

        # Initialize the base RetryTransport with our retry configuration
        super().__init__(retry=retry)

        self.client = client_instance

    async def _retry_operation_async(
        self,
        request: httpx.Request,
        send_method: Callable[..., Coroutine[Any, Any, httpx.Response]],
    ) -> httpx.Response:
        """
        Override the async retry operation to handle 401 and 429 errors specially.

        For 401 errors: refresh token and retry immediately (no sleep)
        For 429 errors: sleep with exponential backoff and retry
        For network errors: sleep and retry
        For other errors: use standard retry logic
        """
        retry = self.retry
        response: Union[httpx.Response, httpx.HTTPError, None] = None

        while True:
            # Handle retry logic if we have a response
            if response is not None:
                logger.warning(
                    "_retry_operation_async retrying request={} response={} retry={}".format(
                        request, response, retry
                    )
                )

                # Handle 401 errors specially - refresh token and retry immediately
                if (
                    isinstance(response, httpx.Response)
                    and response.status_code == HTTPStatus.UNAUTHORIZED
                ):
                    if not retry.is_exhausted():
                        logger.info(
                            "401 response received, attempting authentication refresh"
                        )
                        # Handle the 401 error (refresh token and update headers)
                        await self.client._handle_auth_error()

                        # Update request headers with new auth token
                        if self.client.auth_token:
                            request.headers["Authorization"] = (
                                f"AnaplanAuthToken {self.client.auth_token}"
                            )

                        retry = retry.increment()
                        # Don't sleep for 401 errors - retry immediately
                        response = None
                        continue
                    else:
                        logger.error("Max retries reached for authentication error")
                        return response

                # For all other responses (including HTTP errors), use standard retry logic with sleep
                else:
                    retry = retry.increment()
                    await retry.asleep(response)

            # Attempt the request
            try:
                response = await send_method(request)
            except httpx.HTTPError as e:
                if retry.is_exhausted() or not retry.is_retryable_exception(e):
                    raise

                response = e
                continue

            # Check if we should retry based on status code
            if retry.is_exhausted() or not retry.is_retryable_status_code(
                response.status_code
            ):
                return response


class AnaplanApiClient(BaseClient):
    """Client for Anaplan API interactions with auth token management."""

    def __init__(self, credentials: Dict[str, Any] = {}):
        """Initialize Anaplan API client with credentials."""

        super().__init__(credentials=credentials)
        self.host = credentials.get("host", "us1a.app.anaplan.com")
        self.username = credentials.get("username")
        self.password = credentials.get("password")
        self.auth_type = credentials.get("authType", "basic")

        self.auth_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self._token_lock = asyncio.Lock()  # Prevents concurrent token operations

    async def load(self, **kwargs: Any) -> None:
        """Initialize the client with credentials and necessary attributes."""

        credentials = kwargs.get("credentials", {})
        self.credentials = credentials
        self.host = credentials.get("host", "us1a.app.anaplan.com")
        self.username = credentials.get("username")
        self.password = credentials.get("password")
        self.auth_type = credentials.get("authType", "basic")

        self.auth_token = None
        self.token_expires_at = None

        # Set the auth token and token expiration time
        await self._get_auth_token()

        # Set default headers for all API calls
        self._update_client_headers()

        # Configure custom retry transport for 429 and 401 handling
        self.http_retry_transport = AnaplanRetryTransport(
            client_instance=self,
            total=2,
            backoff_factor=2.0,
            max_backoff_wait=30.0,
            backoff_jitter=0.1,
            respect_retry_after_header=True,
        )

    def _update_client_headers(self) -> None:
        """Update client headers with current authentication token and content type."""

        if self.auth_token:
            self.http_headers = {
                "Authorization": f"AnaplanAuthToken {self.auth_token}",
                "Content-Type": "application/json",
            }
        else:
            # Fallback headers without auth token
            self.http_headers = {"Content-Type": "application/json"}
        logger.debug(f"Updated client headers: {self.http_headers}")

    async def _get_auth_token(self) -> str:
        """
        Get authentication token from Anaplan API using basic auth.
        Thread-safe with async lock to prevent concurrent token operations.

        ------------------------------------------------------------
        Endpoint: POST https://auth.anaplan.com/token/authenticate
        Auth: Basic (username, password) via auth parameter
        Body: None
        Expected Response: 201 Created
        Response Body: {
            "meta": {
                "validationUrl": "https://auth.anaplan.com/token/validate"
            },
            "status": "SUCCESS",
            "statusMessage": "Login successful",
            "tokenInfo": {
                "expiresAt": <timestamp>,
                "tokenId": "<token_id>",
                "tokenValue": "<token_value>",
                "refreshTokenId": "<refresh_token_id>"
            }
        }
        """
        async with self._token_lock:
            # Check if we have a valid token
            if (
                self.auth_token
                and self.token_expires_at
                and datetime.now() < self.token_expires_at
            ):
                logger.debug("Using existing valid token")
                return self.auth_token

            # Check if token is expired but we have one (try refresh first)
            if (
                self.auth_token
                and self.token_expires_at
                and datetime.now() >= self.token_expires_at
            ):
                logger.info("Token expired, attempting refresh")
                try:
                    # Try to refresh the existing token
                    return await self._refresh_auth_token()
                except Exception as e:
                    logger.warning(f"Token refresh failed, will get new token: {e}")
                    # Clear expired token and fall through to get new token
                    self.auth_token = None
                    self.token_expires_at = None

        # Basic auth using the new auth parameter
        if self.auth_type == "basic":
            if not self.username or not self.password:
                raise Exception(
                    "Username and password are required for basic authentication"
                )

            # Use the auth parameter instead of manual base64 encoding
            response = await self.execute_http_post_request(
                "https://auth.anaplan.com/token/authenticate",
                auth=(self.username, self.password),
            )

            if response and response.is_success:  # Success Code : 201
                token_data = response.json()
                token_info = token_data.get("tokenInfo", {})
                self.auth_token = token_info.get("tokenValue")
                if not self.auth_token:
                    raise Exception("Token not found in authentication response")

                # Store token expiration time (Unix timestamp in milliseconds)
                expires_at = token_info.get("expiresAt")
                if expires_at:
                    try:
                        # Convert Unix timestamp (milliseconds) to datetime
                        expires_timestamp = int(expires_at) / 1000  # Convert to seconds
                        self.token_expires_at = datetime.fromtimestamp(
                            expires_timestamp
                        )
                    except Exception as e:
                        logger.warning(
                            f"Could not parse token expiration: {e}, setting default 30 minutes"
                        )
                        self.token_expires_at = datetime.now() + timedelta(minutes=30)
                else:
                    # Default to 30 minutes if no expiration provided
                    self.token_expires_at = datetime.now() + timedelta(minutes=30)

                logger.info(
                    f"Successfully obtained Anaplan authentication token, expires at {self.token_expires_at}"
                )
                return self.auth_token
            else:
                error_msg = f"Authentication failed with status {response.status_code if response else 'No response'}: {response.text if response else 'No response'}"
                logger.error(error_msg)
                raise Exception(error_msg)
        else:
            raise Exception(f"Unsupported authentication type: {self.auth_type}")

    async def _refresh_auth_token(self) -> str:
        """
        Refresh authentication token from Anaplan API.
        Thread-safe with async lock to prevent concurrent refresh operations.

        ------------------------------------------------------------
        Endpoint: POST https://auth.anaplan.com/token/refresh
        Header: Authorization: AnaplanAuthToken <current_token>
        Body: None
        Expected Response: 200 OK
        Response Body: {
            "meta": {
                "validationUrl": "https://auth.anaplan.com/token/validate"
            },
            "status": "SUCCESS",
            "statusMessage": "Token refreshed",
            "tokenInfo": {
                "expiresAt": <timestamp>,
                "tokenId": "<token_id>",
                "tokenValue": "<new_token_value>",
                "refreshTokenId": "<refresh_token_id>"
            }
        }
        """
        async with self._token_lock:
            if not self.auth_token:
                logger.warning("No current token available for refresh")
                raise Exception(
                    "No token available for refresh - use _get_auth_token() to get a new token"
                )

        try:
            response = await self.execute_http_post_request(
                "https://auth.anaplan.com/token/refresh",
            )

            if response and response.is_success:
                token_data = response.json()
                token_info = token_data.get("tokenInfo", {})
                new_token = token_info.get("tokenValue")
                if not new_token:
                    raise Exception("New token not found in refresh response")

                self.auth_token = new_token

                # Update token expiration time (Unix timestamp in milliseconds)
                expires_at = token_info.get("expiresAt")
                if expires_at:
                    try:
                        # Convert Unix timestamp (milliseconds) to datetime
                        expires_timestamp = int(expires_at) / 1000  # Convert to seconds
                        self.token_expires_at = datetime.fromtimestamp(
                            expires_timestamp
                        )
                    except Exception as e:
                        logger.warning(
                            f"Could not parse refresh token expiration: {e}, setting default 30 minutes"
                        )
                        self.token_expires_at = datetime.now() + timedelta(minutes=30)
                else:
                    self.token_expires_at = datetime.now() + timedelta(minutes=30)

                # Update client headers with new token for retries
                self._update_client_headers()

                logger.info(
                    f"Successfully refreshed Anaplan authentication token, expires at {self.token_expires_at}"
                )
                return new_token
            else:
                raise Exception(
                    f"Token refresh failed with status {response.status_code if response else 'No response'}: {response.text if response else 'No response'}"
                )

        except Exception as refresh_error:
            logger.error(f"Failed to refresh token: {str(refresh_error)}")
            logger.warning(
                "Resetting token to None and attempting to create a new token"
            )

            # Reset token and get a new one - when not able to refresh token
            self.auth_token = None
            self.token_expires_at = None
            new_token = await self._get_auth_token()
            if not new_token:
                raise Exception(
                    "Failed to get new token from token reset after refresh failure"
                )

            # Update client headers with new token
            self._update_client_headers()
            return new_token

    async def _handle_auth_error(self) -> None:
        """
        Handle authentication errors by refreshing the token.
        This method is called by the retry transport when a 401 error is encountered.
        """
        logger.info("Handling authentication error - refreshing token")
        await self._refresh_auth_token()
