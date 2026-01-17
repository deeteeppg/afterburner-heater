"""Afterburner Heater protocol module.

Shared protocol definitions for both Home Assistant integration
and standalone protocol lab tool.
"""

from .commands import (
    RefreshCommand,
    RunCommand,
    build_command,
    cyclic_enabled_command,
    cyclic_off_command,
    cyclic_on_command,
    cyclic_temp_command,
    fixed_demand_command,
    frost_enable_command,
    frost_on_command,
    frost_rise_command,
    frost_target_command,
    gpout1_command,
    gpout2_command,
    refresh_command,
    run_command,
    thermostat_command,
    thermostat_mode_command,
)
from .const import (
    CHAR_NOTIFY_UUID,
    CHAR_WRITE_ALT_UUID,
    CHAR_WRITE_UUID,
    DEFAULT_BLE_APPEND_NEWLINE,
    DEFAULT_BLE_COMMAND_TIMEOUT,
    DEFAULT_BLE_CONNECT_TIMEOUT,
    DEFAULT_BLE_INIT_MESSAGE,
    DEFAULT_BLE_WRITE_CHAR,
    DEFAULT_BLE_WRITE_WITH_RESPONSE,
    DEFAULT_WS_COMMAND_TIMEOUT,
    DEFAULT_WS_INIT_MESSAGE,
    DEFAULT_WS_PATH,
    DEFAULT_WS_PORT,
    SERVICE_UUID,
)
from .json_stream import JsonObjectStream
from .models import (
    BOOL_KEYS,
    FLOAT_KEYS,
    INT_KEYS,
    STR_KEYS,
    TEMPERATURE_KEYS,
    HeaterState,
    normalize_payload,
    parse_message,
    raw_bool,
    raw_value,
    state_text_from_raw,
)

__all__ = [
    # JSON stream parser
    "JsonObjectStream",
    # Models and parsing
    "HeaterState",
    "normalize_payload",
    "parse_message",
    "state_text_from_raw",
    "raw_value",
    "raw_bool",
    # Key sets
    "TEMPERATURE_KEYS",
    "BOOL_KEYS",
    "INT_KEYS",
    "FLOAT_KEYS",
    "STR_KEYS",
    # Protocol constants
    "SERVICE_UUID",
    "CHAR_NOTIFY_UUID",
    "CHAR_WRITE_UUID",
    "CHAR_WRITE_ALT_UUID",
    "DEFAULT_WS_PATH",
    "DEFAULT_WS_PORT",
    "DEFAULT_WS_COMMAND_TIMEOUT",
    "DEFAULT_WS_INIT_MESSAGE",
    "DEFAULT_BLE_WRITE_CHAR",
    "DEFAULT_BLE_WRITE_WITH_RESPONSE",
    "DEFAULT_BLE_INIT_MESSAGE",
    "DEFAULT_BLE_APPEND_NEWLINE",
    "DEFAULT_BLE_CONNECT_TIMEOUT",
    "DEFAULT_BLE_COMMAND_TIMEOUT",
    # Commands
    "RefreshCommand",
    "RunCommand",
    "build_command",
    "refresh_command",
    "run_command",
    "cyclic_temp_command",
    "cyclic_on_command",
    "cyclic_off_command",
    "cyclic_enabled_command",
    "frost_enable_command",
    "frost_on_command",
    "frost_rise_command",
    "frost_target_command",
    "thermostat_command",
    "thermostat_mode_command",
    "fixed_demand_command",
    "gpout1_command",
    "gpout2_command",
]
