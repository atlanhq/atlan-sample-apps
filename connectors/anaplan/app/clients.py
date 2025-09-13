from typing import Any

from application_sdk.clients.base import BaseClient
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)

class AppClient(BaseClient):
    """Client for Anaplan API interactions."""

    async def load(self, **kwargs: Any) -> None:
        """Initialize the client with credentials and necessary attributes."""

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

        if self.auth_type == "basic":
            if not self.username or not self.password:
                raise Exception(
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
                    raise Exception("Token not found in authentication response")

                logger.info(
                    "Successfully obtained Anaplan authentication token"
                )
                return self.auth_token
            else:
                error_msg = f"Authentication failed with status {response.status_code if response else 'No response'}: {response.text if response else 'No response'}"
                logger.error(error_msg)
                raise Exception(error_msg)
        else:
            raise Exception(f"Unsupported authentication type: {self.auth_type}")

    async def _update_client_headers(self) -> None:
        """Update client headers with current authentication token and content type."""

        if self.auth_token:
            self.http_headers = {
                "Authorization": f"AnaplanAuthToken {self.auth_token}",
                "Content-Type": "application/json",
            }
        else:
            # Fallback headers without auth token
            self.http_headers = {"Content-Type": "application/json"}
        logger.info("Updated client headers.")