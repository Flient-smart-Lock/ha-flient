"""The Flient Smart Lock integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FlientApi
from .const import (
    DOMAIN,
    HA_CLIENT_ID,
    HA_CLIENT_SECRET,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from .coordinator import FlientCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]


def _register_oauth2(hass: HomeAssistant) -> None:
    """Register OAuth2 implementation if not already registered."""
    config_entry_oauth2_flow.async_register_implementation(
        hass,
        DOMAIN,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            client_id=HA_CLIENT_ID,
            client_secret=HA_CLIENT_SECRET,
            authorize_url=OAUTH2_AUTHORIZE,
            token_url=OAUTH2_TOKEN,
        ),
    )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Flient component."""
    _register_oauth2(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Flient from a config entry."""
    # Ensure OAuth2 is registered (async_setup may not have been called)
    _register_oauth2(hass)

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )
    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    session = async_get_clientsession(hass)
    api = FlientApi(session, oauth_session)

    coordinator = FlientCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
