"""Battery Emulator: MQTT bridge for cell-level sensors (BMS card friendly)."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_TOPIC_PREFIX, CONF_USE_BATTERY_2, DOMAIN
from .hub import BatteryEmulatorMqttHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hub = BatteryEmulatorMqttHub(
        hass,
        entry.entry_id,
        entry.data[CONF_TOPIC_PREFIX],
        entry.data.get(CONF_USE_BATTERY_2, False),
    )
    await hub.async_start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hub: BatteryEmulatorMqttHub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.async_stop()
    return unload_ok
