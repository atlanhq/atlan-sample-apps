from typing import Any

from application_sdk.clients.base import BaseClient
from application_sdk.common.error_codes import ClientError
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class AppClient(BaseClient):
    """Client for App API interactions.

    Handles authentication and HTTP requests to App (Anaplan) APIs.
    Supports basic authentication with token-based authorization.
    """

    async def load(self, **kwargs: Any) -> None:
        """Initialize the client with credentials and necessary attributes.

        Args:
            **kwargs: Keyword arguments containing credentials and configuration.
        """

        credentials = kwargs.get("credentials", {})
        self.credentials = credentials
        self.host = credentials.get("host", "us1a.app.anaplan.com")
        self.username = credentials.get("username")
        self.password = credentials.get("password")
        self.auth_type = credentials.get("authType", "basic")

        self.auth_token = None

        # Set the auth token and token expiration time
        await self._get_auth_token()

        # Set default headers for all API calls
        await self._update_client_headers()

    async def _get_auth_token(self) -> str:
        """Get authentication token from Anaplan API using basic auth.

        Makes a POST request to Anaplan's authentication endpoint to obtain
        an authentication token for subsequent API calls.

        Returns:
            str: The authentication token value.

        Raises:
            Exception: If authentication fails or token is not found in response.

        Note:
            Endpoint: POST https://auth.anaplan.com/token/authenticate
            Expected Response: 201 Created with token information.
        """

        if self.auth_type == "basic":
            if not self.username or not self.password:
                raise ClientError(
                    "Username and password are required for basic authentication"
                )

            # Pass the auth parameters to BaseClient's execute_http_post_request
            response = await self.execute_http_post_request(
                "https://auth.anaplan.com/token/authenticate",
                auth=(self.username, self.password),
            )

            if response and response.is_success:  # Success Code : 201
                token_data = response.json()
                token_info = token_data.get("tokenInfo", {})
                self.auth_token = token_info.get("tokenValue")
                if not self.auth_token:
                    raise ClientError("Token not found in authentication response")

                logger.info("Successfully obtained Anaplan authentication token")
                return self.auth_token
            else:
                error_msg = f"Authentication failed with status {response.status_code if response else 'No response'}: {response.text if response else 'No response'}"
                logger.error(error_msg)
                raise ClientError(error_msg)
        else:
            raise ClientError(f"Unsupported authentication type: {self.auth_type}")

    async def _update_client_headers(self) -> None:
        """Update client headers with current authentication token and content type.

        Sets the Authorization header with the Anaplan auth token and Content-Type
        header for JSON requests.
        """

        if self.auth_token:
            self.http_headers = {
                "Authorization": f"AnaplanAuthToken {self.auth_token}",
                "Content-Type": "application/json",
            }
        else:
            # Fallback headers without auth token
            self.http_headers = {"Content-Type": "application/json"}
        logger.info("Updated client headers.")
