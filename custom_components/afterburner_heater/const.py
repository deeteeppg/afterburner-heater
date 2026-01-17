"""Afterburner Heater constants.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "afterburner_heater"
NAME = "Afterburner Heater"

CONF_TRANSPORT = "transport"
CONF_BLE_WRITE_CHAR = "ble_write_char"
CONF_BLE_WRITE_WITH_RESPONSE = "ble_write_with_response"
CONF_BLE_INIT_MESSAGE = "ble_init_message"
CONF_BLE_APPEND_NEWLINE = "ble_append_newline"
CONF_WS_INIT_MESSAGE = "ws_init_message"

TRANSPORT_BLE = "ble"
TRANSPORT_WEBSOCKET = "websocket"

# Heater sends periodic updates (IP_STARSSI, Pressure, Humidity) automatically
# every ~10-13s. Full state refresh only needed for less-frequently-changing
# values like thermostat settings, GPIO state, and error codes.
DEFAULT_POLL_INTERVAL = timedelta(seconds=60)

# Transport-specific poll intervals:
# - BLE: Shorter interval since heater doesn't push state changes over BLE
# - WebSocket: Longer interval since heater pushes updates automatically
DEFAULT_POLL_INTERVAL_BLE = timedelta(seconds=30)
DEFAULT_POLL_INTERVAL_WS = timedelta(seconds=60)
DEFAULT_WS_PATH = "/"
DEFAULT_WS_PORT = 81
DEFAULT_BLE_WRITE_CHAR = "FFE1"
DEFAULT_BLE_WRITE_WITH_RESPONSE = True
DEFAULT_BLE_INIT_MESSAGE = {"Refresh": 1}
DEFAULT_BLE_APPEND_NEWLINE = False
DEFAULT_BLE_CONNECT_TIMEOUT = 10
DEFAULT_BLE_COMMAND_TIMEOUT = 5
DEFAULT_WS_INIT_MESSAGE = {"Refresh": 1}

SERVICE_SEND_JSON = "send_json"
SERVICE_SET_CYCLIC_TEMP = "set_cyclic_temp"
SERVICE_SET_CYCLIC_ON = "set_cyclic_on"
SERVICE_SET_CYCLIC_OFF = "set_cyclic_off"
SERVICE_SET_CYCLIC_ENABLED = "set_cyclic_enabled"
SERVICE_SET_FROST_ENABLE = "set_frost_enable"
SERVICE_SET_FROST_ON = "set_frost_on"
SERVICE_SET_FROST_RISE = "set_frost_rise"
SERVICE_SET_FROST_TARGET = "set_frost_target"
SERVICE_SET_THERMOSTAT = "set_thermostat"
SERVICE_SET_THERMOSTAT_MODE = "set_thermostat_mode"
SERVICE_SET_FIXED_DEMAND = "set_fixed_demand"
SERVICE_SET_GPOUT1 = "set_gpout1"
SERVICE_SET_GPOUT2 = "set_gpout2"

SERVICE_UUID = "FFE0"
CHAR_NOTIFY_UUID = "FFE1"
CHAR_WRITE_UUID = "FFE1"
CHAR_WRITE_ALT_UUID = "FFE2"

ATTR_PAYLOAD = "payload"
ATTR_CMD = "cmd"
ATTR_VALUE = "value"

REDACTED_CONFIG = {"access_token", "password", "token"}

# Fields that the heater updates periodically without needing a Refresh command.
# These arrive every ~10-13 seconds via push notifications.
PERIODIC_UPDATE_FIELDS = frozenset({
    "IP_STARSSI",   # WiFi signal strength (dBm)
    "Pressure",     # Barometric pressure
    "Humidity",     # Relative humidity
})
