"""The Flient Smart Lock integration."""
from __future__ import annotations

import logging

from aiohttp import web

from homeassistant.components.webhook import async_register as webhook_register, async_unregister as webhook_unregister
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FlientApi
from .const import DOMAIN, WEBHOOK_ID_KEY
from .coordinator import FlientCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Flient from a config entry."""
    session = async_get_clientsession(hass)
    api = FlientApi(
        session,
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        user_id=entry.data.get("user_id"),
    )

    coordinator = FlientCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register webhook for real-time lock state updates
    webhook_id = f"flient_{entry.entry_id}"
    webhook_register(
        hass,
        DOMAIN,
        "Flient Lock Events",
        webhook_id,
        _handle_webhook,
    )
    hass.data[DOMAIN][WEBHOOK_ID_KEY] = webhook_id

    # Register webhook URL with Flient backend
    webhook_url = f"{get_url(hass)}/api/webhook/{webhook_id}"
    _LOGGER.info("Flient webhook registered: %s", webhook_url)
    try:
        await api.register_webhook(webhook_url)
    except Exception:
        _LOGGER.warning("Failed to register webhook with Flient backend")

    return True


def get_url(hass: HomeAssistant) -> str:
    """Get the HA external or internal URL."""
    try:
        return hass.config.external_url or hass.config.internal_url or f"http://{hass.config.api.host}:{hass.config.api.port}"
    except Exception:
        return "http://homeassistant.local:8123"


async def _handle_webhook(hass: HomeAssistant, webhook_id: str, request: web.Request) -> web.Response:
    """Handle incoming webhook from Flient backend."""
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400)

    lock_id = data.get("lock_id")
    state = data.get("state")  # 0=locked, 1=unlocked
    event_type = data.get("event_type")  # lock/unlock
    user = data.get("user", "")
    method = data.get("method", "")

    _LOGGER.debug("Flient webhook: lock=%s state=%s event=%s user=%s method=%s", lock_id, state, event_type, user, method)

    if lock_id is None:
        return web.Response(status=400)

    # Find coordinator and update state
    for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
        if entry_id == WEBHOOK_ID_KEY:
            continue
        if isinstance(coordinator, FlientCoordinator) and coordinator.data:
            if lock_id in coordinator.data:
                coordinator.data[lock_id]["state"] = state
                coordinator.data[lock_id]["last_user"] = user
                coordinator.data[lock_id]["last_method"] = method
                coordinator.async_set_updated_data(coordinator.data)
                break

    return web.Response(status=200)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    webhook_id = hass.data.get(DOMAIN, {}).get(WEBHOOK_ID_KEY)
    if webhook_id:
        webhook_unregister(hass, webhook_id)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
