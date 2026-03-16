"""Data coordinator for Flient Smart Lock."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FlientApi, FlientApiError, FlientAuthError
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class FlientCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Coordinator to manage fetching Flient lock data."""

    def __init__(self, hass: HomeAssistant, api: FlientApi) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api = api

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Fetch lock list from the API (no per-lock state calls)."""
        try:
            locks = await self.api.get_locks()
        except FlientAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except FlientApiError as err:
            raise UpdateFailed(f"Error communicating with Flient API: {err}") from err

        lock_data: dict[int, dict[str, Any]] = {}
        for lock in locks:
            lock_id = lock.get("lock_id")
            if lock_id is None:
                continue

            # Preserve existing state data if we have it
            existing = self.data.get(lock_id, {}) if self.data else {}
            merged = {**lock}
            if "state" in existing:
                merged["state"] = existing["state"]
            if "auto_lock_time" in existing:
                merged["auto_lock_time"] = existing["auto_lock_time"]

            lock_data[lock_id] = merged

        return lock_data

    async def async_refresh_lock_state(self, lock_id: int) -> dict[str, Any]:
        """Fetch state for a single lock on demand."""
        try:
            state = await self.api.get_lock_state(lock_id)
            if self.data and lock_id in self.data:
                self.data[lock_id].update(state)
            return state
        except FlientApiError as err:
            _LOGGER.warning("Failed to get state for lock %s: %s", lock_id, err)
            return {}
