"""MQTT subscription hub for Battery Emulator topics."""

from __future__ import annotations

import json
import logging
import inspect
from collections.abc import Callable
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    SIGNAL_UPDATE,
    TOPIC_SUFFIX_BALANCING,
    TOPIC_SUFFIX_BALANCING_2,
    TOPIC_SUFFIX_INFO,
    TOPIC_SUFFIX_SPEC,
    TOPIC_SUFFIX_SPEC_2,
)

_LOGGER = logging.getLogger(__name__)


def update_signal(entry_id: str) -> str:
    return f"{SIGNAL_UPDATE}_{entry_id}"


class BatteryEmulatorMqttHub:
    """Subscribes to Battery Emulator MQTT topics and holds last payloads."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        topic_prefix: str,
        use_battery_2: bool,
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.topic_prefix = topic_prefix.strip().strip("/")
        self.use_battery_2 = use_battery_2
        self.info: dict[str, Any] = {}
        self.cell_volts: dict[int, list[float]] = {}
        self.cell_balancing: dict[int, list[bool]] = {}
        self._unsub: list[Callable[[], None]] = []
        self._on_cell_topology_change: list[Callable[[], None]] = []

    def set_cell_topology_listener(self, cb: Callable[[], None]) -> None:
        self._on_cell_topology_change.append(cb)

    def _notify_topology(self) -> None:
        for cb in self._on_cell_topology_change:
            if inspect.iscoroutinefunction(cb):
                self.hass.async_create_task(cb())
            else:
                cb()

    @callback
    def _mqtt_message(self, msg: ReceiveMessage) -> None:
        topic = msg.topic
        prefix = self.topic_prefix
        raw = msg.payload
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
            _LOGGER.debug("Ignoring non-JSON payload on %s", topic)
            return

        if not isinstance(payload, dict):
            return

        if topic == f"{prefix}{TOPIC_SUFFIX_INFO}":
            self.info = payload
        elif topic == f"{prefix}{TOPIC_SUFFIX_SPEC}":
            self._parse_spec(payload, battery_index=1)
        elif topic == f"{prefix}{TOPIC_SUFFIX_SPEC_2}":
            self._parse_spec(payload, battery_index=2)
        elif topic == f"{prefix}{TOPIC_SUFFIX_BALANCING}":
            self._parse_balancing(payload, battery_index=1)
        elif topic == f"{prefix}{TOPIC_SUFFIX_BALANCING_2}":
            self._parse_balancing(payload, battery_index=2)
        else:
            return

        async_dispatcher_send(self.hass, update_signal(self.entry_id))

    def _parse_spec(self, payload: dict[str, Any], battery_index: int) -> None:
        raw = payload.get("cell_voltages")
        if not isinstance(raw, list):
            return
        prev = len(self.cell_volts.get(battery_index, ()))
        try:
            volts = [float(x) for x in raw]
        except (TypeError, ValueError):
            return
        self.cell_volts[battery_index] = volts
        if len(volts) != prev:
            self._notify_topology()

    def _parse_balancing(self, payload: dict[str, Any], battery_index: int) -> None:
        raw = payload.get("cell_balancing")
        if not isinstance(raw, list):
            return
        try:
            bal = [bool(x) for x in raw]
        except (TypeError, ValueError):
            return
        prev = len(self.cell_balancing.get(battery_index, ()))
        self.cell_balancing[battery_index] = bal
        if len(bal) != prev:
            self._notify_topology()

    async def async_start(self) -> None:
        topics = [
            f"{self.topic_prefix}{TOPIC_SUFFIX_INFO}",
            f"{self.topic_prefix}{TOPIC_SUFFIX_SPEC}",
            f"{self.topic_prefix}{TOPIC_SUFFIX_BALANCING}",
        ]
        if self.use_battery_2:
            topics.append(f"{self.topic_prefix}{TOPIC_SUFFIX_SPEC_2}")
            topics.append(f"{self.topic_prefix}{TOPIC_SUFFIX_BALANCING_2}")

        for t in topics:
            unsub = await mqtt.async_subscribe(self.hass, t, self._mqtt_message, qos=0)
            self._unsub.append(unsub)

    async def async_stop(self) -> None:
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()
