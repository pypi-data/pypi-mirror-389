"""Simple OIDC client using AuthLib."""

import logging
from typing import Optional

import aiohttp
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc6749 import OAuth2Token


class OAuth2Client:
    def __init__(
        self,
        client_id: str,
        authorization_endpoint: str,
        token_endpoint: str,
        redirect_uri: str = "http://localhost:3000",
    ):
        self.client_id = client_id
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.redirect_uri = redirect_uri + "/callback"
        self.logger = logging.getLogger(__name__)

        # In-memory token storage only
        self.access_token: Optional[str] = None

        # Initialize OAuth2 session
        self.session = OAuth2Session(
            client_id=client_id,
            redirect_uri=self.redirect_uri,
            scope=f"openid email profile offline_access {client_id}",
        )

    def ensure_valid_access_token(self) -> bool:
        """Check if we have a valid access token in memory."""
        if self.access_token:
            self.logger.info("Valid access token found in memory")
            return True

        self.logger.info("No valid access token in memory")
        return False

    def get_authorization_url(self) -> str:
        """Get the authorization URL for OAuth2 flow."""
        try:
            authorization_url, _ = self.session.create_authorization_url(
                self.authorization_endpoint
            )
            self.logger.info("Generated authorization URL")
            return str(authorization_url)
        except Exception as e:
            self.logger.error(f"Failed to create authorization URL: {e}")
            raise

    def exchange_code_for_tokens(self, authorization_code: str) -> OAuth2Token:
        """Exchange authorization code for access token."""
        try:
            token = self.session.fetch_token(
                url=self.token_endpoint,
                code=authorization_code,
                client_id=self.client_id,
            )
            # Store token in memory
            self.access_token = token["access_token"]
            self.logger.info("Successfully exchanged code for tokens")
            return token
        except Exception as e:
            self.logger.error(f"Failed to exchange code for tokens: {e}")
            raise

    def get_authenticated_session(self) -> aiohttp.ClientSession:
        """Get an aiohttp session with authentication headers."""

        if not self.access_token:
            raise ValueError("No authentication token available")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        return aiohttp.ClientSession(headers=headers)
