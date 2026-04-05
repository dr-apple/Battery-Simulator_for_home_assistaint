"""Sensors derived from Battery Emulator /info and per-cell /spec_data."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_BATTERY_INDEX, CONF_USE_BATTERY_2, DOMAIN
from .hub import BatteryEmulatorMqttHub, update_signal


def _bat_suffix(battery_index: int) -> str:
    return "_2" if battery_index == 2 else ""


def _name_suffix(battery_index: int) -> str:
    return " 2" if battery_index == 2 else ""


# Fields published in mqtt.cpp set_battery_attributes + globals on /info
def _battery_field_descriptions(
    battery_index: int,
) -> tuple[SensorEntityDescription, ...]:
    ns = _name_suffix(battery_index)
    sk = _bat_suffix(battery_index)
    return (
        SensorEntityDescription(
            key=f"SOC{sk}",
            name=f"SOC{ns}",
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.BATTERY,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        SensorEntityDescription(
            key=f"SOC_real{sk}",
            name=f"SOC (real){ns}",
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.BATTERY,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        SensorEntityDescription(
            key=f"state_of_health{sk}",
            name=f"State of health{ns}",
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.BATTERY,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        SensorEntityDescription(
            key=f"temperature_min{sk}",
            name=f"Temperature min{ns}",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        SensorEntityDescription(
            key=f"temperature_max{sk}",
            name=f"Temperature max{ns}",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        SensorEntityDescription(
            key=f"stat_batt_power{sk}",
            name=f"Battery power{ns}",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"battery_current{sk}",
            name=f"Battery current{ns}",
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=2,
        ),
        SensorEntityDescription(
            key=f"battery_voltage{sk}",
            name=f"Battery voltage{ns}",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=2,
        ),
        SensorEntityDescription(
            key=f"cell_max_voltage{sk}",
            name=f"Cell max voltage{ns}",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=3,
        ),
        SensorEntityDescription(
            key=f"cell_min_voltage{sk}",
            name=f"Cell min voltage{ns}",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=3,
        ),
        SensorEntityDescription(
            key=f"cell_voltage_delta{sk}",
            name=f"Cell voltage delta{ns}",
            native_unit_of_measurement="mV",
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=0,
        ),
        SensorEntityDescription(
            key=f"total_capacity{sk}",
            name=f"Total capacity{ns}",
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY_STORAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"remaining_capacity{sk}",
            name=f"Remaining capacity{ns}",
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY_STORAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"remaining_capacity_real{sk}",
            name=f"Remaining capacity (real){ns}",
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY_STORAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"max_discharge_power{sk}",
            name=f"Max discharge power{ns}",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"max_charge_power{sk}",
            name=f"Max charge power{ns}",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"charged_energy{sk}",
            name=f"Charged energy{ns}",
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key=f"discharged_energy{sk}",
            name=f"Discharged energy{ns}",
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key=f"balancing_active_cells{sk}",
            name=f"Balancing active cells{ns}",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"balancing_status{sk}",
            name=f"Balancing status{ns}",
        ),
    )


GLOBAL_SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="bms_status",
        name="BMS status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="pause_status",
        name="Pause status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="event_level",
        name="Event level",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="emulator_status",
        name="Emulator status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="emulator_uptime",
        name="Emulator uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="cpu_temp",
        name="CPU temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_INFO_TEXT_KEYS = frozenset(
    {
        "bms_status",
        "pause_status",
        "event_level",
        "emulator_status",
        "balancing_status",
        "balancing_status_2",
    }
)


class BatteryEmulatorInfoSensor(SensorEntity):
    """Single field from the JSON /info topic."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hub: BatteryEmulatorMqttHub,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        self._hub = hub
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
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
    def native_value(self) -> str | float | int | None:
        raw = self._hub.info.get(self.entity_description.key)
        if raw is None:
            return None
        key = self.entity_description.key
        if key in _INFO_TEXT_KEYS:
            return str(raw)
        if key.startswith("balancing_active_cells"):
            try:
                return int(float(raw))
            except (TypeError, ValueError):
                return None
        if self.entity_description.native_unit_of_measurement is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None
        return str(raw)


class BatteryEmulatorCellSensor(SensorEntity):
    """One Li-ion cell voltage (for BMS Battery Cells Card)."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

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
        ns = _name_suffix(battery_index)
        self._attr_name = f"Cell {cell_number}{ns}"
        self._attr_unique_id = (
            f"{entry.entry_id}_bat{battery_index}_cell_{cell_number}"
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
    def native_value(self) -> float | None:
        cells = self._hub.cell_volts.get(self._battery_index, [])
        if self._cell_index >= len(cells):
            return None
        return cells[self._cell_index]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub: BatteryEmulatorMqttHub = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for desc in GLOBAL_SENSOR_DESCRIPTIONS:
        entities.append(BatteryEmulatorInfoSensor(hub, entry, desc))

    for desc in _battery_field_descriptions(1):
        entities.append(BatteryEmulatorInfoSensor(hub, entry, desc))

    if entry.data.get(CONF_USE_BATTERY_2):
        for desc in _battery_field_descriptions(2):
            entities.append(BatteryEmulatorInfoSensor(hub, entry, desc))

    async_add_entities(entities)

    batteries = [1]
    if entry.data.get(CONF_USE_BATTERY_2):
        batteries.append(2)

    added: dict[int, int] = {1: 0, 2: 0}

    def ensure_cell_sensors() -> None:
        to_add: list[SensorEntity] = []
        for bi in batteries:
            n = len(hub.cell_volts.get(bi, ()))
            while added[bi] < n:
                added[bi] += 1
                to_add.append(
                    BatteryEmulatorCellSensor(hub, entry, bi, added[bi]),
                )
        if to_add:
            async_add_entities(to_add)

    hub.set_cell_topology_listener(ensure_cell_sensors)
    ensure_cell_sensors()
