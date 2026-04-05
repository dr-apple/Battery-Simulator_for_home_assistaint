"""Per-cell balancing state from Battery Emulator /balancing_data topics."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_BATTERY_INDEX, CONF_USE_BATTERY_2, DOMAIN
from .hub import BatteryEmulatorMqttHub, update_signal


class BatteryEmulatorCellBalanceBinarySensor(BinarySensorEntity):
    """Balancing active for one cell (optional input for BMS Battery Cells Card)."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(
        self,
        hub: BatteryEmulatorMqttHub,
        entry: ConfigEntry,
        battery_index: int,
        cell_number: int,
    ) -> None:
        self._hub = hub
        self._entry = entry
        self._battery_index = battery_index
        self._cell_index = cell_number - 1
        suffix = " 2" if battery_index == 2 else ""
        self._attr_name = f"Cell {cell_number} balancing{suffix}"
        self._attr_unique_id = (
            f"{entry.entry_id}_bat{battery_index}_balance_{cell_number}"
        )
        self._attr_extra_state_attributes = {ATTR_BATTERY_INDEX: battery_index}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data["name"],
            manufacturer="DalaTech",
            model="Battery Emulator",
            configuration_url="https://github.com/dalathegreat/Battery-Emulator",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                update_signal(self._entry.entry_id),
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        cells = self._hub.cell_balancing.get(self._battery_index, [])
        if self._cell_index >= len(cells):
            return None
        return bool(cells[self._cell_index])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub: BatteryEmulatorMqttHub = hass.data[DOMAIN][entry.entry_id]
    batteries = [1]
    if entry.data.get(CONF_USE_BATTERY_2):
        batteries.append(2)

    added: dict[int, int] = {1: 0, 2: 0}

    def ensure_balance_entities() -> None:
        to_add: list[BinarySensorEntity] = []
        for bi in batteries:
            n = len(hub.cell_balancing.get(bi, ()))
            while added[bi] < n:
                added[bi] += 1
                to_add.append(
                    BatteryEmulatorCellBalanceBinarySensor(hub, entry, bi, added[bi]),
                )
        if to_add:
            async_add_entities(to_add)

    hub.set_cell_topology_listener(ensure_balance_entities)
    ensure_balance_entities()
