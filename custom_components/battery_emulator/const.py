"""Constants for Battery Emulator MQTT integration."""

DOMAIN = "battery_emulator"

CONF_TOPIC_PREFIX = "topic_prefix"
CONF_USE_BATTERY_2 = "use_battery_2"

DEFAULT_TOPIC_PREFIX = "BE"

TOPIC_SUFFIX_INFO = "/info"
TOPIC_SUFFIX_SPEC = "/spec_data"
TOPIC_SUFFIX_SPEC_2 = "/spec_data_2"
TOPIC_SUFFIX_BALANCING = "/balancing_data"
TOPIC_SUFFIX_BALANCING_2 = "/balancing_data_2"

SIGNAL_UPDATE = f"{DOMAIN}_update"

ATTR_BATTERY_INDEX = "battery_index"
