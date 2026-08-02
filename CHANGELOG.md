# Changelog

All notable changes to this project are documented in this file.

## [1.1.0] - 2026-08-02

### Fixed

- Added native read-only binary sensors for charging, discharging, and balancing so the detailed BMS card no longer shows all three states as permanently off.
- Added support for Battery Emulator v11 MQTT topics, including hostname-based topic prefixes, the separate `info_2` topic, and balancing flags embedded in `spec_data`.
- Preserved compatibility with Battery Emulator v10 and older payloads that use suffixed battery-2 fields and separate `balancing_data` topics.
- Corrected boolean parsing so text values such as `"false"` are not interpreted as active.
- Removed the inappropriate battery device class from per-cell balancing entities.

### Added

- Added a Home Assistant reconfigure flow for changing the MQTT hostname/topic prefix without removing and recreating the integration.
- Added Charging State and Limiting Factor sensors exposed by Battery Emulator v11.
- Added six unit tests covering charge/discharge inference, balancing fallbacks, boolean parsing, and v10/v11 battery-2 payload normalization.
- Added troubleshooting guidance for stale MQTT discovery entities and guarded legacy `value_json` templates.

### Changed

- Updated the supplied BMS Battery Cells Card configuration to reference the three native status binary sensors.
- Updated English and German setup text for the Battery Emulator v11 hostname migration.
- Corrected the integration documentation and issue-tracker links.

### Upgrade notes

- Battery Emulator v11 users must configure the integration's MQTT topic prefix to the emulator hostname, for example `battery-emulator-a1b2`.
- If Home Assistant logs `value_json is undefined`, remove stale or manually created MQTT-discovery status entities after disabling Home Assistant Autodiscovery in Battery Emulator. This integration's native status sensors do not use Jinja templates.
- After upgrading through HACS, restart Home Assistant and copy the three `stat_*_entity` entries from `dashboard-bms-battery-cells-card.yaml` into existing card configurations.

### Validation

- Six unit tests passed.
- Python byte-compilation completed successfully.
- Manifest, strings, and translation JSON files were validated.
- Legacy templates were evaluated without `value_json` in Home Assistant and returned `OFF` without logging an error.
