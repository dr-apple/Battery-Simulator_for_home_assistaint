# Battery Emulator (Home Assistant)

Custom Integration für [Battery Emulator](https://github.com/dalathegreat/Battery-Emulator): liest die MQTT-Topics (`{Präfix}/info`, `{Präfix}/spec_data`, `{Präfix}/balancing_data`) und legt **eine Sensor-Entität pro Zelle** an. Damit lässt sich die [BMS Battery Cells Card](https://github.com/jayjojayson/bms-battery-cells-card) direkt befüllen.

## Voraussetzungen

- Home Assistant mit konfigurierter **MQTT-Integration** (Broker muss die Nachrichten des Battery Emulator empfangen).
- Im Battery Emulator: MQTT aktiv; **„Transmit all cell voltages“** (`mqtt_transmit_all_cellvoltages`) einschalten, sonst fehlen `spec_data` / Zellspannungen.

## Installation (HACS)

1. HACS → **Integrationen** → ⋮ → **Benutzerdefiniertes Repository**.
2. URL dieses Repositories einfügen, Kategorie **Integration**.
3. **Battery Emulator** installieren und Home Assistant neu starten.

## Einrichtung

**Einstellungen → Geräte & Dienste → Integration hinzufügen → Battery Emulator**

Im Assistenten: MQTT-Topic-Präfix wie im Web-UI des Boards (Standard `BE`), Gerätename, optional zweites Pack.

## BMS Battery Cells Card (Beispiel)

Entitäts-IDs nach Installation aus **Entwicklerwerkzeuge** übernehmen (Prefix hängt vom Gerätenamen ab).

```yaml
type: custom:bms-battery-cells-card
title: Batteriezellen
cells:
  - entity: sensor.battery_emulator_cell_1
    name: "1"
  - entity: sensor.battery_emulator_cell_2
    name: "2"
  # … alle Zellen
soc_entity: sensor.battery_emulator_soc
watt_entity: sensor.battery_emulator_battery_power
cell_diff_sensor: sensor.battery_emulator_cell_voltage_delta
temp_entity: sensor.battery_emulator_temperature_max
min_voltage: 2.6
max_voltage: 3.65
```

Optional pro Zelle Balancing: Entität `binary_sensor...._cell_N_balancing` in der Kartenkonfiguration als Balance-Sensor setzen (siehe Karten-Dokumentation).

## Doppelte Entitäten

Wenn im Battery Emulator **Home Assistant Autodiscovery** aktiv ist, legt der Broker zusätzlich MQTT-Discovery-Sensoren an. Diese Integration erzeugt eigene Entitäten für die BMS-Karte. Entweder Autodiscovery im Emulator deaktivieren oder die nicht benötigten MQTT-Entitäten ignorieren/deaktivieren.

## Hinweis

Hohe Spannung an Batterien birgt Risiken. Nur nach geltenden Vorschriften und mit Fachkenntnis arbeiten.

Passe in `manifest.json` das Feld `codeowners` auf deinen GitHub-Benutzernamen an, bevor du das Repository veröffentlichst.
