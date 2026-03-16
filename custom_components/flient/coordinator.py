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
        self._initial_load = True

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Fetch lock data. First call loads list, subsequent calls poll events."""
        try:
            if self._initial_load or not self.data:
                # First load: get lock list
                locks = await self.api.get_locks()
                lock_data: dict[int, dict[str, Any]] = {}
                for lock in locks:
                    lock_id = lock.get("lock_id")
                    if lock_id is None:
                        continue
                    lock_data[lock_id] = lock
                self._initial_load = False
                return lock_data

            # Subsequent calls: check for recent events
            events = await self.api.get_events(since=SCAN_INTERVAL_SECONDS + 10)
            if events:
                for event in events:
                    lock_id = event.get("lock_id")
                    if lock_id and lock_id in self.data:
                        event_type = event.get("event_type")
                        if event_type == "lock":
                            self.data[lock_id]["state"] = 0
                        elif event_type == "unlock":
                            self.data[lock_id]["state"] = 1
                        self.data[lock_id]["last_method"] = event.get("method", "")
                        self.data[lock_id]["last_event_time"] = event.get("timestamp", "")

            return self.data

        except FlientAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except FlientApiError as err:
            raise UpdateFailed(f"Error communicating with Flient API: {err}") from err

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
