"""Config flow for OpenClaw Conversation Agent."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import aiohttp

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("manager_url", default="https://openclaw-manager.eulencode.de"): str,
        vol.Required("device_token"): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect to OpenClaw Manager."""
    
    manager_url = data["manager_url"].rstrip("/")
    device_token = data["device_token"]
    
    # Test connection to OpenClaw Manager
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{manager_url}/api/v1/voice/device/info",
                headers={"Authorization": f"Bearer {device_token}"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    raise CannotConnect(f"Failed to connect: HTTP {response.status}")
                
                device_info = await response.json()
                return {
                    "title": f"Kaspar ({device_info['name']} - {device_info['location']})",
                    "device_id": device_info["deviceId"]
                }
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise CannotConnect from err

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenClaw Conversation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
