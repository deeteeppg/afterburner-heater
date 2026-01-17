"""Afterburner Heater integration.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_ADDRESS,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api.ble import BleHeaterApi
from .api.ws import WebSocketHeaterApi
from .const import (
    ATTR_CMD,
    ATTR_PAYLOAD,
    ATTR_VALUE,
    CONF_BLE_WRITE_CHAR,
    CONF_BLE_WRITE_WITH_RESPONSE,
    CONF_BLE_INIT_MESSAGE,
    CONF_BLE_APPEND_NEWLINE,
    CONF_WS_INIT_MESSAGE,
    CONF_TRANSPORT,
    DEFAULT_BLE_WRITE_CHAR,
    DEFAULT_BLE_WRITE_WITH_RESPONSE,
    DEFAULT_BLE_INIT_MESSAGE,
    DEFAULT_BLE_APPEND_NEWLINE,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL_BLE,
    DEFAULT_POLL_INTERVAL_WS,
    DEFAULT_WS_PATH,
    DEFAULT_WS_INIT_MESSAGE,
    DOMAIN,
    SERVICE_SEND_JSON,
    SERVICE_SET_CYCLIC_ENABLED,
    SERVICE_SET_CYCLIC_OFF,
    SERVICE_SET_CYCLIC_ON,
    SERVICE_SET_CYCLIC_TEMP,
    SERVICE_SET_FROST_ENABLE,
    SERVICE_SET_FROST_ON,
    SERVICE_SET_FROST_RISE,
    SERVICE_SET_FROST_TARGET,
    SERVICE_SET_FIXED_DEMAND,
    SERVICE_SET_GPOUT1,
    SERVICE_SET_GPOUT2,
    SERVICE_SET_THERMOSTAT,
    SERVICE_SET_THERMOSTAT_MODE,
    TRANSPORT_BLE,
    TRANSPORT_WEBSOCKET,
)
from .coordinator import AfterburnerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Afterburner Heater from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    transport = entry.data[CONF_TRANSPORT]

    # Use transport-specific default poll interval
    if transport == TRANSPORT_BLE:
        default_interval = DEFAULT_POLL_INTERVAL_BLE
    elif transport == TRANSPORT_WEBSOCKET:
        default_interval = DEFAULT_POLL_INTERVAL_WS
    else:
        default_interval = DEFAULT_POLL_INTERVAL

    update_seconds = entry.options.get(
        CONF_SCAN_INTERVAL, int(default_interval.total_seconds())
    )
    update_interval = timedelta(seconds=update_seconds)

    coordinator: AfterburnerCoordinator

    def _message_callback(payload: dict[str, Any]) -> None:
        coordinator.handle_message(payload)

    if transport == TRANSPORT_BLE:
        address = entry.data[CONF_ADDRESS]
        write_char = entry.options.get(
            CONF_BLE_WRITE_CHAR, DEFAULT_BLE_WRITE_CHAR
        )
        write_with_response = entry.options.get(
            CONF_BLE_WRITE_WITH_RESPONSE, DEFAULT_BLE_WRITE_WITH_RESPONSE
        )
        append_newline = entry.options.get(
            CONF_BLE_APPEND_NEWLINE, DEFAULT_BLE_APPEND_NEWLINE
        )
        init_message = _parse_init_message(
            entry.options.get(
                CONF_BLE_INIT_MESSAGE, json.dumps(DEFAULT_BLE_INIT_MESSAGE)
            ),
            "BLE",
        )
        api = BleHeaterApi(
            hass,
            address,
            write_char,
            write_with_response,
            _message_callback,
            init_message=init_message,
            append_newline=append_newline,
        )
    elif transport == TRANSPORT_WEBSOCKET:
        host = entry.data[CONF_HOST]
        port = entry.data.get(CONF_PORT)
        path = entry.options.get(CONF_PATH, entry.data.get(CONF_PATH, DEFAULT_WS_PATH))
        init_message = _parse_init_message(
            entry.options.get(
                CONF_WS_INIT_MESSAGE, json.dumps(DEFAULT_WS_INIT_MESSAGE)
            ),
            "WebSocket",
        )
        token = entry.data.get(CONF_ACCESS_TOKEN)
        api = WebSocketHeaterApi(
            hass,
            host,
            port,
            path,
            _message_callback,
            token=token,
            init_message=init_message,
        )
    else:
        raise UpdateFailed(f"Unsupported transport: {transport}")

    coordinator = AfterburnerCoordinator(hass, entry, api, update_interval)
    await coordinator.async_start()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
        "transport": transport,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        await coordinator.async_stop()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SEND_JSON):
        return

    async def _async_send_payload(payload_obj: dict[str, Any]) -> None:
        tasks = []
        for entry_data in hass.data.get(DOMAIN, {}).values():
            api = entry_data.get("api")
            if api:
                tasks.append(api.async_send_json(payload_obj))
        if tasks:
            await asyncio.gather(*tasks)

    async def _handle_send_json(call: ServiceCall) -> None:
        cmd = call.data.get(ATTR_CMD)
        value = call.data.get(ATTR_VALUE)
        payload = call.data.get(ATTR_PAYLOAD)

        if cmd is not None:
            if payload is not None:
                raise vol.Invalid("Provide either payload or cmd/value")
            if value is None:
                raise vol.Invalid("cmd requires value")
            payload_obj = {cmd: value}
        else:
            if payload is None:
                raise vol.Invalid("payload is required when cmd is not provided")
            if isinstance(payload, str):
                try:
                    payload_obj = json.loads(payload)
                except json.JSONDecodeError as err:
                    raise vol.Invalid("Invalid JSON payload") from err
            elif isinstance(payload, dict):
                payload_obj = payload
            else:
                raise vol.Invalid("Payload must be JSON string or dict")

        await _async_send_payload(payload_obj)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_JSON,
        _handle_send_json,
        schema=vol.Schema(
            {
                vol.Exclusive(ATTR_PAYLOAD, "payload_or_cmd"): vol.Any(str, dict),
                vol.Exclusive(ATTR_CMD, "payload_or_cmd"): str,
                ATTR_VALUE: object,
            }
        ),
    )

    def _register_simple_service(
        service_name: str,
        cmd_key: str,
        value_schema: vol.Schema,
    ) -> None:
        async def _handler(call: ServiceCall) -> None:
            value = call.data.get("value")
            if value is None:
                raise vol.Invalid("value is required")
            await _async_send_payload({cmd_key: value})

        hass.services.async_register(
            DOMAIN,
            service_name,
            _handler,
            schema=value_schema,
        )

    _register_simple_service(
        SERVICE_SET_CYCLIC_TEMP,
        "CyclicTemp",
        vol.Schema({vol.Required("value"): vol.Coerce(float)}),
    )
    _register_simple_service(
        SERVICE_SET_CYCLIC_ON,
        "CyclicOn",
        vol.Schema({vol.Required("value"): vol.Coerce(float)}),
    )
    _register_simple_service(
        SERVICE_SET_CYCLIC_OFF,
        "CyclicOff",
        vol.Schema({vol.Required("value"): vol.Coerce(float)}),
    )
    _register_simple_service(
        SERVICE_SET_CYCLIC_ENABLED,
        "CyclicEnb",
        vol.Schema({vol.Required("value"): vol.Coerce(int)}),
    )
    _register_simple_service(
        SERVICE_SET_FROST_ENABLE,
        "FrostEnable",
        vol.Schema({vol.Required("value"): vol.Coerce(int)}),
    )
    _register_simple_service(
        SERVICE_SET_FROST_ON,
        "FrostOn",
        vol.Schema({vol.Required("value"): vol.Coerce(float)}),
    )
    _register_simple_service(
        SERVICE_SET_FROST_RISE,
        "FrostRise",
        vol.Schema({vol.Required("value"): vol.Coerce(float)}),
    )
    _register_simple_service(
        SERVICE_SET_FROST_TARGET,
        "FrostTarget",
        vol.Schema({vol.Required("value"): vol.Coerce(float)}),
    )
    _register_simple_service(
        SERVICE_SET_THERMOSTAT,
        "Thermostat",
        vol.Schema({vol.Required("value"): vol.Coerce(int)}),
    )
    _register_simple_service(
        SERVICE_SET_THERMOSTAT_MODE,
        "ThermostatMode",
        vol.Schema({vol.Required("value"): str}),
    )
    _register_simple_service(
        SERVICE_SET_FIXED_DEMAND,
        "FixedDemand",
        vol.Schema({vol.Required("value"): vol.Any(vol.Coerce(float), None)}),
    )
    _register_simple_service(
        SERVICE_SET_GPOUT1,
        "GPout1",
        vol.Schema({vol.Required("value"): vol.Coerce(int)}),
    )
    _register_simple_service(
        SERVICE_SET_GPOUT2,
        "GPout2",
        vol.Schema({vol.Required("value"): vol.Coerce(int)}),
    )


def _parse_init_message(value: str | None, transport: str) -> dict[str, Any] | None:
    """Parse an init message JSON string for any transport type.

    Args:
        value: JSON string to parse.
        transport: Transport name for logging (e.g., "WebSocket", "BLE").

    Returns:
        Parsed dict or None if invalid.
    """
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        _LOGGER.warning("Invalid %s init JSON; ignoring", transport)
        return None
    if not isinstance(parsed, dict):
        _LOGGER.warning("%s init JSON must be an object; ignoring", transport)
        return None
    return parsed
