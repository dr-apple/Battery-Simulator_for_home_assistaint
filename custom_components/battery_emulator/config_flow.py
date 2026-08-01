"""Config flow for Battery Emulator."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.mqtt import DOMAIN as MQTT_DOMAIN
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_TOPIC_PREFIX, CONF_USE_BATTERY_2, DEFAULT_TOPIC_PREFIX, DOMAIN


class BatteryEmulatorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle UI-based setup (wizard)."""

    VERSION = 1

    @staticmethod
    def _schema(defaults: dict) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_TOPIC_PREFIX,
                    default=defaults.get(CONF_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX),
                ): str,
                vol.Required(
                    "name", default=defaults.get("name", "Battery Emulator")
                ): str,
                vol.Optional(
                    CONF_USE_BATTERY_2,
                    default=defaults.get(CONF_USE_BATTERY_2, False),
                ): bool,
            }
        )

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if not self.hass.config_entries.async_entries(MQTT_DOMAIN):
            return self.async_abort(reason="mqtt_not_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            prefix = user_input[CONF_TOPIC_PREFIX].strip().strip("/")
            name = user_input["name"].strip() or "Battery Emulator"
            if not prefix:
                errors["base"] = "invalid_prefix"
            else:
                await self.async_set_unique_id(prefix)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_TOPIC_PREFIX: prefix,
                        "name": name,
                        CONF_USE_BATTERY_2: user_input[CONF_USE_BATTERY_2],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=self._schema({}), errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Allow changing the MQTT hostname/topic after a v11 upgrade."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            prefix = user_input[CONF_TOPIC_PREFIX].strip().strip("/")
            name = user_input["name"].strip() or "Battery Emulator"
            if not prefix:
                errors["base"] = "invalid_prefix"
            else:
                data = {
                    CONF_TOPIC_PREFIX: prefix,
                    "name": name,
                    CONF_USE_BATTERY_2: user_input[CONF_USE_BATTERY_2],
                }
                return self.async_update_reload_and_abort(
                    entry,
                    title=name,
                    unique_id=prefix,
                    data_updates=data,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._schema(dict(entry.data)),
            errors=errors,
        )
