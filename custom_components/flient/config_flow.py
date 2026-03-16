"""Config flow for Flient Smart Lock."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .const import API_BASE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class FlientConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Flient."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                user_data = await self._validate_credentials(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                user_id = user_data.get("user_id", user_input[CONF_EMAIL])
                await self.async_set_unique_id(str(user_id))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Flient Smart Lock",
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        "user_id": user_id,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _validate_credentials(self, email: str, password: str) -> dict:
        """Validate the user credentials against Flient API."""
        url = f"{API_BASE_URL}/ha/login"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={"email": email, "password": password},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth
                    if resp.status != 200:
                        raise CannotConnect
                    data = await resp.json()
                    if data.get("status") != 1:
                        raise InvalidAuth
                    return data.get("data", {})
        except InvalidAuth:
            raise
        except CannotConnect:
            raise
        except aiohttp.ClientError as err:
            raise CannotConnect from err


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
