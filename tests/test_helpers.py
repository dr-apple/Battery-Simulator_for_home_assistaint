"""Tests for MQTT parsing and dashboard status helpers."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HELPERS_PATH = Path(__file__).parents[1] / "custom_components" / "battery_emulator" / "helpers.py"
SPEC = importlib.util.spec_from_file_location("battery_emulator_helpers", HELPERS_PATH)
assert SPEC is not None and SPEC.loader is not None
helpers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helpers)


class HelpersTest(unittest.TestCase):
    def test_parse_bool_handles_string_false(self) -> None:
        self.assertFalse(helpers.parse_bool("false"))
        self.assertFalse(helpers.parse_bool("off"))
        self.assertTrue(helpers.parse_bool("true"))
        self.assertTrue(helpers.parse_bool(1))

    def test_charging_state_from_v11_field(self) -> None:
        info = {"charging_state": "Discharging"}
        self.assertFalse(helpers.charging_status(info, 1, "charging"))
        self.assertTrue(helpers.charging_status(info, 1, "discharging"))

    def test_v11_secondary_info_is_normalized_and_preserved(self) -> None:
        info = helpers.merge_info_payload({"SOC": 50}, {"SOC": 80, "battery_current": -4}, 2)
        self.assertEqual(info["SOC"], 50)
        self.assertEqual(info["SOC_2"], 80)
        self.assertEqual(info["battery_current_2"], -4)

        info = helpers.merge_info_payload(info, {"SOC": 51}, 1)
        self.assertEqual(info["SOC"], 51)
        self.assertEqual(info["SOC_2"], 80)

    def test_legacy_primary_info_refreshes_secondary_values(self) -> None:
        info = helpers.merge_info_payload({"SOC": 50, "SOC_2": 80}, {"SOC": 51, "SOC_2": 81}, 1)
        self.assertEqual(info["SOC_2"], 81)

    def test_charging_state_falls_back_to_current(self) -> None:
        self.assertTrue(helpers.charging_status({"battery_current": -12.5}, 1, "discharging"))
        self.assertTrue(helpers.charging_status({"battery_current_2": 4.2}, 2, "charging"))

    def test_balancing_state_fallbacks(self) -> None:
        self.assertTrue(helpers.balancing_status({"balancing_status": "Active"}, {}, 1))
        self.assertTrue(helpers.balancing_status({}, {1: [False, True]}, 1))
        self.assertIsNone(helpers.balancing_status({}, {}, 1))


if __name__ == "__main__":
    unittest.main()
