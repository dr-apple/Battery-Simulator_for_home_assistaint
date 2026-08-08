"""Home Assistant 2026.8 compatibility tests."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.battery_emulator.const import DOMAIN
from custom_components.battery_emulator.hub import BatteryEmulatorMqttHub
from custom_components.battery_emulator.sensor import (
    GLOBAL_SENSOR_DESCRIPTIONS,
    BatteryEmulatorInfoSensor,
)


def test_topology_listener_can_be_removed(hass: HomeAssistant) -> None:
    """Dynamic entity callbacks do not remain registered after unloading."""
    hub = BatteryEmulatorMqttHub(hass, "entry", "BE", False)
    calls = 0

    def listener() -> None:
        nonlocal calls
        calls += 1

    remove = hub.add_cell_topology_listener(listener)
    hub._notify_topology()
    remove()
    hub._notify_topology()

    assert calls == 1


def test_non_finite_sensor_values_are_rejected(hass: HomeAssistant) -> None:
    """NaN and infinity are not written to Home Assistant sensor states."""
    entry = MockConfigEntry(domain=DOMAIN, data={"name": "Battery Emulator"})
    hub = BatteryEmulatorMqttHub(hass, entry.entry_id, "BE", False)
    description = next(item for item in GLOBAL_SENSOR_DESCRIPTIONS if item.key == "cpu_temp")
    sensor = BatteryEmulatorInfoSensor(hub, entry, description)

    hub.info["cpu_temp"] = "nan"
    assert sensor.native_value is None
    hub.info["cpu_temp"] = "inf"
    assert sensor.native_value is None
    hub.info["cpu_temp"] = "24.5"
    assert sensor.native_value == 24.5
