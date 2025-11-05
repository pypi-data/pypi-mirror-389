"""
Keycloak HTTP Client.

This module contains the KeycloakHttpClient class that handles all HTTP
interactions with the Keycloak server.
"""

from typing import Any, Optional

import httpx

from ..config import KeycloakConfig


class KeycloakHttpClient:
    """HTTP client for Keycloak API."""

    def __init__(self, config: KeycloakConfig):
        """Initialize the Keycloak HTTP client."""
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                headers={
                    "User-Agent": "lks-idprovider-keycloak/0.1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_well_known_config(self) -> dict[str, Any]:
        """Get the well-known OpenID Connect configuration."""
        self._ensure_client()
        if not self._client:
            raise RuntimeError("HTTP client is not initialized")
        response = await self._client.get(
            f"/realms/{self.config.realm}/.well-known/openid-configuration"
        )
        response.raise_for_status()
        return response.json()

    async def introspect_token(self, token: str) -> dict[str, Any]:
        """Validate a token using the OIDC introspection endpoint.

        Returns:
            A dictionary containing the token's introspection results.
        """
        self._ensure_client()
        if not self._client:
            raise RuntimeError("HTTP client is not initialized")

        data = {
            "token": token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        response = await self._client.post(
            f"/realms/{self.config.realm}/protocol/openid-connect/token/introspect",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()

    async def get_userinfo(self, token: str) -> dict[str, Any]:
        """Get user info from the userinfo endpoint using the provided access token."""
        self._ensure_client()
        if not self._client:
            raise RuntimeError("HTTP client is not initialized")
        response = await self._client.get(
            self.config.userinfo_endpoint,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()
