"""Sensor platform for Flient Smart Lock."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
    """Set up Flient sensors from a config entry."""
    coordinator: FlientCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for lock_id, lock_data in coordinator.data.items():
        entities.append(FlientBatterySensor(coordinator, lock_id, lock_data))

    async_add_entities(entities)


class FlientBatterySensor(CoordinatorEntity[FlientCoordinator], SensorEntity):
    """Battery sensor for a Flient Smart Lock."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: FlientCoordinator,
        lock_id: int,
        lock_data: dict[str, Any],
    ) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator)
        self._lock_id = lock_id
        self._attr_unique_id = f"flient_battery_{lock_id}"
        self._attr_name = "Batterij"

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
    def native_value(self) -> int | None:
        """Return the battery level."""
        lock_data = self.coordinator.data.get(self._lock_id, {})
        return (
            lock_data.get("battery_level")
            or lock_data.get("electricQuantity")
            or lock_data.get("battery_percentage")
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
