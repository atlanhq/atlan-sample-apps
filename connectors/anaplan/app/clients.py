import base64
from typing import Any

from app.constants import AnaplanUrls
from app.models import AnaplanAuthResponse, AnaplanCredentials, AuthType
from application_sdk.clients.base import BaseClient
from application_sdk.common.error_codes import ClientError
from application_sdk.common.utils import (
    download_file_from_upload_response,
    parse_credentials_extra,
)
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class AppClient(BaseClient):
    """Client for App API interactions.

    Handles authentication and HTTP requests to App (Anaplan) APIs.
    Supports basic authentication and CA Certificate authentication with
    token-based authorization.
    """

    async def load(self, **kwargs: Any) -> None:
        """Initialize the client with credentials and necessary attributes.

        Args:
            **kwargs: Keyword arguments containing credentials and configuration.
        """

        credentials = kwargs.get("credentials", {})
        self.credentials = credentials

        creds = AnaplanCredentials.model_validate(credentials)
        self.host = creds.host
        self.auth_type = creds.authType

        self.auth_token = None
        self.cert_path: str | None = None

        match creds.authType:
            case AuthType.BASIC:
                self.username = creds.username
                self.password = creds.password
            case AuthType.CA_CERT:
                self.username = creds.username
                self.password = creds.password
                extra = parse_credentials_extra(credentials)
                cert_metadata = extra.get("CaCertificate")
                if not cert_metadata:
                    raise ClientError(
                        "CA Certificate is required for ca_cert authentication"
                    )
                self.cert_path = await download_file_from_upload_response(cert_metadata)

        # Set the auth token
        await self._get_auth_token()

        # Set default headers for all API calls
        self._update_client_headers()

    async def _get_auth_token(self) -> str:
        """Get authentication token from Anaplan API.

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

        if self.auth_type == AuthType.BASIC:
            if not self.username or not self.password:
                raise ClientError(
                    "Username and password are required for basic authentication"
                )

            response = await self.execute_http_post_request(
                AnaplanUrls.AUTH_AUTHENTICATE,
                auth=(self.username, self.password),
            )

        elif self.auth_type == AuthType.CA_CERT:
            if not self.cert_path:
                raise ClientError(
                    "CA Certificate is required for ca_cert authentication"
                )

            with open(self.cert_path, "rb") as f:
                cert_b64 = base64.b64encode(f.read()).decode()

            response = await self.execute_http_post_request(
                AnaplanUrls.AUTH_AUTHENTICATE,
                headers={"Authorization": f"CACertificate {cert_b64}"},
                json_data={
                    "encodedData": self.username,
                    "encodedSignedData": self.password,
                },
            )

        else:
            raise ClientError(f"Unsupported authentication type: {self.auth_type}")

        if response and response.is_success:  # Success Code : 201
            auth_response = AnaplanAuthResponse.model_validate(response.json())
            self.auth_token = auth_response.tokenInfo.tokenValue
            logger.info("Successfully obtained Anaplan authentication token")
            return self.auth_token
        else:
            error_msg = f"Authentication failed with status {response.status_code if response else 'No response'}: {response.text if response else 'No response'}"
            logger.error(error_msg)
            raise ClientError(error_msg)

    def _update_client_headers(self) -> None:
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
