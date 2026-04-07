"""Config flow for AC Mitsubishi (Modbus RTU over TCP)."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DEFAULT_PORT, DOMAIN, INTEGRATION_VERSION
from .modbus import ModbusRTUClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
    }
)


class MitsubishiACConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup UI for AC Mitsubishi."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = int(user_input[CONF_PORT])

            # Prevent duplicate entries for the same host:port
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            # Test connectivity
            client = ModbusRTUClient(host, port)
            if await client.connect():
                await client.close()
            else:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"AC Mitsubishi v{INTEGRATION_VERSION} ({host})",
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
