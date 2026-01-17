"""Protocol constants for Afterburner Heater.

These are transport-level constants shared between the HA integration
and standalone protocol tools.
"""

from __future__ import annotations

# BLE Service and Characteristic UUIDs
SERVICE_UUID = "FFE0"
CHAR_NOTIFY_UUID = "FFE1"
CHAR_WRITE_UUID = "FFE1"
CHAR_WRITE_ALT_UUID = "FFE2"

# WebSocket defaults
DEFAULT_WS_PATH = "/"
DEFAULT_WS_PORT = 81
DEFAULT_WS_COMMAND_TIMEOUT = 10
DEFAULT_WS_INIT_MESSAGE: dict[str, int] = {"Refresh": 1}

# BLE defaults
DEFAULT_BLE_WRITE_CHAR = "FFE1"
DEFAULT_BLE_WRITE_WITH_RESPONSE = True
DEFAULT_BLE_INIT_MESSAGE: dict[str, int] = {"Refresh": 1}
DEFAULT_BLE_APPEND_NEWLINE = False
DEFAULT_BLE_CONNECT_TIMEOUT = 10
DEFAULT_BLE_COMMAND_TIMEOUT = 5
