"""Lock platform for Flient Smart Lock."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FlientCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Flient locks from a config entry."""
    coordinator: FlientCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FlientLock(coordinator, lock_id, lock_data)
        for lock_id, lock_data in coordinator.data.items()
    ]

    async_add_entities(entities)


class FlientLock(CoordinatorEntity[FlientCoordinator], LockEntity):
    """Representation of a Flient Smart Lock."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FlientCoordinator,
        lock_id: int,
        lock_data: dict[str, Any],
    ) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._lock_id = lock_id
        self._attr_unique_id = f"flient_lock_{lock_id}"
        self._attr_name = lock_data.get("lock_name", f"Lock {lock_id}")
        self._attr_is_locked = True  # Default to locked
        self._is_locking = False
        self._is_unlocking = False

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        lock_data = self.coordinator.data.get(self._lock_id, {})
        return {
            "identifiers": {(DOMAIN, str(self._lock_id))},
            "name": lock_data.get("lock_name", f"Flient Lock {self._lock_id}"),
            "manufacturer": "Flient",
            "model": lock_data.get("lock_model", "Smart Lock"),
        }

    @property
    def is_locked(self) -> bool | None:
        """Return true if the lock is locked."""
        lock_data = self.coordinator.data.get(self._lock_id, {})
        state = lock_data.get("state")
        if state is not None:
            # Flient API: 0 = locked, 1 = unlocked, 2 = unknown
            if state == 2:
                return self._attr_is_locked
            return state == 0
        return self._attr_is_locked

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        lock_data = self.coordinator.data.get(self._lock_id, {})
        attrs = {}
        auto_lock = lock_data.get("auto_lock_time")
        if auto_lock is not None:
            attrs["auto_lock_time"] = auto_lock
            attrs["auto_lock_enabled"] = auto_lock > 0
        return attrs

    @property
    def is_locking(self) -> bool:
        """Return true if the lock is locking."""
        return self._is_locking

    @property
    def is_unlocking(self) -> bool:
        """Return true if the lock is unlocking."""
        return self._is_unlocking

    async def async_added_to_hass(self) -> None:
        """Fetch state when entity is added."""
        await super().async_added_to_hass()
        # Fetch state on demand when entity first loads
        await self.coordinator.async_refresh_lock_state(self._lock_id)
        self.async_write_ha_state()

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        self._is_locking = True
        self.async_write_ha_state()

        success = await self.coordinator.api.lock(self._lock_id)

        self._is_locking = False
        if success:
            self._attr_is_locked = True

        self.async_write_ha_state()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        self._is_unlocking = True
        self.async_write_ha_state()

        success = await self.coordinator.api.unlock(self._lock_id)

        self._is_unlocking = False
        if success:
            self._attr_is_locked = False
            # Schedule re-lock based on auto_lock_time
            lock_data = self.coordinator.data.get(self._lock_id, {})
            auto_lock = lock_data.get("auto_lock_time", 0)
            if auto_lock and auto_lock > 0:
                self.hass.async_create_task(self._auto_lock_refresh(auto_lock + 2))

        self.async_write_ha_state()

    async def _auto_lock_refresh(self, delay: int) -> None:
        """Refresh state after auto-lock delay."""
        await asyncio.sleep(delay)
        # Fetch real state from API
        await self.coordinator.async_refresh_lock_state(self._lock_id)
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
