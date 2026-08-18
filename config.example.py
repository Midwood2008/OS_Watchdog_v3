"""
Local configuration template.

Copy this file to config.py. Never commit config.py.
"""

# MQTT
MQTT_BROKER = "mqtt.example.local"
MQTT_PORT = 1883
MQTT_USER = "your-mqtt-username"
MQTT_PASS = "your-mqtt-password"
MQTT_TOPIC = "milesight/uplink/#"

# Pushover
PUSHOVER_USER = "your-pushover-user-key"
PUSHOVER_TOKEN = "your-pushover-app-token"

# Timing, in seconds
POLL_INTERVAL = 60
WATCHDOG_CHECK_INTERVAL = 10
MISMATCH_DELAY = 300
LORAWAN_STALE_TIME = 1200
OS_STALE_TIME = 300

# OpenSprinkler controllers
OPENSPRINKLERS = [
    {
        "name": "Example Controller",
        "ip": "192.168.1.100",
        "password_md5": "your-opensprinkler-password-md5",
    },
]

# Maps a zero-based OpenSprinkler station to a LoRaWAN relay.
WATCHDOG_MAP = [
    {
        "controller": "Example Controller",
        "station_index": 0,
        "station_name": "Example Station",
        "devEUI": "0000000000000000",
        "relay": "RO1",
    },
]


def normalize_config():
    """Validate and normalise configuration before starting the runtime."""
    required_controller_fields = {"name", "ip", "password_md5"}
    required_mapping_fields = {
        "controller",
        "station_index",
        "station_name",
        "devEUI",
        "relay",
    }

    controller_names = set()
    for controller in OPENSPRINKLERS:
        missing = required_controller_fields - controller.keys()
        if missing:
            raise ValueError(f"Controller is missing fields: {sorted(missing)}")

        if controller["name"] in controller_names:
            raise ValueError(f"Duplicate controller name: {controller['name']}")

        controller_names.add(controller["name"])

    mapping_keys = set()
    for mapping in WATCHDOG_MAP:
        missing = required_mapping_fields - mapping.keys()
        if missing:
            raise ValueError(f"Mapping is missing fields: {sorted(missing)}")

        if mapping["controller"] not in controller_names:
            raise ValueError(
                f"Unknown controller in WATCHDOG_MAP: {mapping['controller']}"
            )

        mapping["station_index"] = int(mapping["station_index"])
        if mapping["station_index"] < 0:
            raise ValueError("station_index must be zero or greater")

        mapping["devEUI"] = mapping["devEUI"].strip().lower()
        mapping["relay"] = mapping["relay"].strip().upper()

        if mapping["relay"] not in ("RO1", "RO2"):
            raise ValueError(f"Invalid relay: {mapping['relay']}")

        key = (
            mapping["controller"],
            mapping["station_index"],
            mapping["devEUI"],
            mapping["relay"],
        )
        if key in mapping_keys:
            raise ValueError(f"Duplicate WATCHDOG_MAP entry: {key}")

        mapping_keys.add(key)
