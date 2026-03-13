"""Config flow for Flient Smart Lock using OAuth2."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN

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

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for the flow."""
        # Use the token data to identify the user
        token = data.get("token", {})
        user_id = token.get("user_id", "unknown")

        await self.async_set_unique_id(str(user_id))
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="Flient Smart Lock",
            data=data,
        )
