"""Config flow for Flient Smart Lock using OAuth2."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    DOMAIN,
    HA_CLIENT_ID,
    HA_CLIENT_SECRET,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)

_LOGGER = logging.getLogger(__name__)


class FlientOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a config flow for Flient via OAuth2."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data to include in the authorize URL."""
        return {"response_type": "code"}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        # Ensure OAuth2 implementation is registered
        config_entry_oauth2_flow.async_register_implementation(
            self.hass,
            DOMAIN,
            config_entry_oauth2_flow.LocalOAuth2Implementation(
                self.hass,
                DOMAIN,
                client_id=HA_CLIENT_ID,
                client_secret=HA_CLIENT_SECRET,
                authorize_url=OAUTH2_AUTHORIZE,
                token_url=OAUTH2_TOKEN,
            ),
        )
        return await super().async_step_user(user_input)

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for the flow."""
        token = data.get("token", {})
        user_id = token.get("user_id", "unknown")

        await self.async_set_unique_id(str(user_id))
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="Flient Smart Lock",
            data=data,
        )
