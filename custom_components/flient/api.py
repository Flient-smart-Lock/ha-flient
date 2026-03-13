"""Flient API client for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class FlientApiError(Exception):
    """Flient API error."""


class FlientAuthError(FlientApiError):
    """Flient authentication error."""


class FlientApi:
    """Client for the Flient API using OAuth2 tokens."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        oauth_session: OAuth2Session,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._oauth_session = oauth_session

    @property
    def _token(self) -> str:
        """Get the current access token."""
        return self._oauth_session.token.get("access_token", "")

    async def get_locks(self) -> list[dict[str, Any]]:
        """Get all locks for the user."""
        resp = await self._request("GET", "ha/locks")
        if resp.get("status") != 1:
            raise FlientApiError(resp.get("message", "Failed to get locks"))
        return resp.get("data", [])

    async def lock(self, lock_id: int) -> bool:
        """Lock via gateway."""
        return await self._lock_action(lock_id, "lock")

    async def unlock(self, lock_id: int) -> bool:
        """Unlock via gateway."""
        return await self._lock_action(lock_id, "unlock")

    async def get_lock_state(self, lock_id: int) -> dict[str, Any]:
        """Get lock state and battery."""
        resp = await self._request("GET", f"ha/lock/{lock_id}/state")
        if resp.get("status") != 1:
            return {}
        return resp.get("data", {})

    async def _lock_action(self, lock_id: int, action: str) -> bool:
        """Perform lock/unlock action."""
        data = {"lock_id": lock_id}
        resp = await self._request("POST", f"ha/lock/{action}", data=data)

        if resp.get("status") != 1:
            _LOGGER.error(
                "Gateway %s failed for lock %s: %s",
                action, lock_id, resp.get("message", "Unknown error"),
            )
            return False
        return True

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated API request."""
        # Ensure token is valid
        await self._oauth_session.async_ensure_token_valid()

        url = f"{API_BASE_URL}/{endpoint}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}",
        }

        try:
            kwargs: dict[str, Any] = {
                "headers": headers,
                "timeout": aiohttp.ClientTimeout(total=30),
            }
            if method == "POST" and data:
                kwargs["json"] = data

            async with self._session.request(method, url, **kwargs) as resp:
                if resp.status == 401:
                    raise FlientAuthError("Authentication expired")
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise FlientApiError(f"API request failed: {err}") from err
