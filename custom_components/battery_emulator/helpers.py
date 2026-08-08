"""Dependency-free parsing helpers for Battery Emulator MQTT payloads."""

from __future__ import annotations

from typing import Any


def parse_bool(value: Any) -> bool:
    """Parse JSON-like boolean values without treating "false" as true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "on", "active", "balancing"}:
            return True
        if normalized in {"0", "false", "off", "inactive", "idle"}:
            return False
    raise ValueError(f"Unsupported boolean value: {value!r}")


def info_key(key: str, battery_index: int) -> str:
    """Return the normalized info key for a battery index."""
    return f"{key}_2" if battery_index == 2 else key


def merge_info_payload(
    current: dict[str, Any], payload: dict[str, Any], battery_index: int
) -> dict[str, Any]:
    """Normalize legacy combined and v11 per-battery info payloads."""
    if battery_index == 2:
        return {**current, **{f"{key}_2": value for key, value in payload.items()}}

    preserved_battery_2 = {
        key: value for key, value in current.items() if key.endswith("_2") and key not in payload
    }
    return {**payload, **preserved_battery_2}


def charging_status(info: dict[str, Any], battery_index: int, expected_state: str) -> bool | None:
    """Return whether a battery is charging or discharging."""
    state = info.get(info_key("charging_state", battery_index))
    if state is not None:
        return str(state).strip().lower() == expected_state

    current = info.get(info_key("battery_current", battery_index))
    try:
        current_value = float(current)
    except (TypeError, ValueError):
        return None
    return current_value > 0 if expected_state == "charging" else current_value < 0


def balancing_status(
    info: dict[str, Any],
    cell_balancing: dict[int, list[bool]],
    battery_index: int,
) -> bool | None:
    """Return whether any balancing is active for a battery."""
    state = info.get(info_key("balancing_status", battery_index))
    if state is not None:
        return str(state).strip().lower() == "active"

    active_cells = info.get(info_key("balancing_active_cells", battery_index))
    if active_cells is not None:
        try:
            return float(active_cells) > 0
        except (TypeError, ValueError):
            return None

    cells = cell_balancing.get(battery_index)
    return any(cells) if cells is not None else None
