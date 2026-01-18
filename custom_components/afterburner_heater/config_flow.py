"""Config flow for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

import json
import logging
from typing import Any

import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_ADDRESS,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CHAR_WRITE_ALT_UUID,
    CHAR_WRITE_UUID,
    CONF_BLE_WRITE_CHAR,
    CONF_BLE_WRITE_WITH_RESPONSE,
    CONF_BLE_INIT_MESSAGE,
    CONF_BLE_APPEND_NEWLINE,
    CONF_TRANSPORT,
    DEFAULT_BLE_WRITE_CHAR,
    DEFAULT_BLE_WRITE_WITH_RESPONSE,
    DEFAULT_BLE_INIT_MESSAGE,
    DEFAULT_BLE_APPEND_NEWLINE,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_WS_PATH,
    DEFAULT_WS_PORT,
    CONF_WS_INIT_MESSAGE,
    DEFAULT_WS_INIT_MESSAGE,
    DOMAIN,
    SERVICE_UUID,
    TRANSPORT_BLE,
    TRANSPORT_WEBSOCKET,
)

_LOGGER = logging.getLogger(__name__)

CONF_MANUAL_ADDRESS = "manual_address"


class AfterburnerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Afterburner Heater."""

    VERSION = 1

    def __init__(self) -> None:
        self._transport: str | None = None
        self._discovered_ble: dict[str, str] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {vol.Required(CONF_TRANSPORT): vol.In([TRANSPORT_BLE, TRANSPORT_WEBSOCKET])}
                ),
            )

        self._transport = user_input[CONF_TRANSPORT]
        if self._transport == TRANSPORT_BLE:
            return await self.async_step_ble()
        return await self.async_step_websocket()

    async def async_step_ble(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is None:
            await self._async_discover_ble()
            data_schema = self._ble_schema()
            return self.async_show_form(
                step_id="ble",
                data_schema=data_schema,
                errors=errors,
            )

        address = user_input.get(CONF_MANUAL_ADDRESS) or user_input.get(CONF_ADDRESS)
        if not address:
            errors["base"] = "invalid_address"
            return self.async_show_form(
                step_id="ble",
                data_schema=self._ble_schema(),
                errors=errors,
            )

        await self.async_set_unique_id(f"ble_{address}")
        self._abort_if_unique_id_configured()

        title = self._discovered_ble.get(address, f"Afterburner {address}")
        return self.async_create_entry(
            title=title,
            data={
                CONF_TRANSPORT: TRANSPORT_BLE,
                CONF_ADDRESS: address,
            },
        )

    async def async_step_websocket(
        self, user_input: dict[str, Any] | None = None
    ):
        errors: dict[str, str] = {}
        if user_input is None:
            return self.async_show_form(
                step_id="websocket",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_HOST): str,
                        vol.Optional(CONF_PORT, default=DEFAULT_WS_PORT): int,
                        vol.Optional(CONF_PATH, default=DEFAULT_WS_PATH): str,
                        vol.Optional(CONF_ACCESS_TOKEN): str,
                    }
                ),
                errors=errors,
            )

        host = user_input[CONF_HOST]
        port = user_input.get(CONF_PORT, DEFAULT_WS_PORT)
        path = user_input.get(CONF_PATH, DEFAULT_WS_PATH)
        token = user_input.get(CONF_ACCESS_TOKEN)

        # Test WebSocket connection before creating entry
        if not await self._test_websocket_connection(host, port, path, token):
            errors["base"] = "cannot_connect"
            return self.async_show_form(
                step_id="websocket",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_HOST, default=host): str,
                        vol.Optional(CONF_PORT, default=port): int,
                        vol.Optional(CONF_PATH, default=path): str,
                        vol.Optional(CONF_ACCESS_TOKEN): str,
                    }
                ),
                errors=errors,
            )

        unique = f"ws_{host}:{port}"
        await self.async_set_unique_id(unique)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Afterburner {host}",
            data={
                CONF_TRANSPORT: TRANSPORT_WEBSOCKET,
                CONF_HOST: host,
                CONF_PORT: port,
                CONF_PATH: path,
                CONF_ACCESS_TOKEN: token,
            },
        )

    async def _test_websocket_connection(
        self, host: str, port: int, path: str, token: str | None
    ) -> bool:
        """Test WebSocket connection to verify host is reachable."""
        if not path.startswith("/"):
            path = f"/{path}"
        url = f"ws://{host}:{port}{path}"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        session = async_get_clientsession(self.hass)
        try:
            async with async_timeout.timeout(10):
                async with session.ws_connect(url, headers=headers) as ws:
                    await ws.close()
            return True
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("WebSocket connection test failed: %s", err)
            return False

    @callback
    def _ble_schema(self) -> vol.Schema:
        if self._discovered_ble:
            return vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(self._discovered_ble),
                    vol.Optional(CONF_MANUAL_ADDRESS): str,
                }
            )
        return vol.Schema({vol.Required(CONF_ADDRESS): str})

    async def _async_discover_ble(self) -> None:
        discovered = {}
        for info in bluetooth.async_discovered_service_info(self.hass):
            if info.name and info.name.startswith("Afterburner"):
                discovered[info.address] = info.name
                continue
            if _has_service_uuid(info, SERVICE_UUID):
                discovered[info.address] = info.name or info.address
        self._discovered_ble = discovered

    async def async_step_import(self, user_input: dict[str, Any]):
        return await self.async_step_user(user_input)

    async def async_step_reauth(self, user_input: dict[str, Any] | None = None):
        return self.async_abort(reason="reauth_not_supported")

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        return self.async_abort(reason="reauth_not_supported")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return AfterburnerOptionsFlowHandler(config_entry)


class AfterburnerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Afterburner Heater options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        transport = self._entry.data[CONF_TRANSPORT]
        options = dict(self._entry.options)
        update_seconds = options.get(
            CONF_SCAN_INTERVAL, int(DEFAULT_POLL_INTERVAL.total_seconds())
        )
        if transport == TRANSPORT_BLE:
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=update_seconds): int,
                    vol.Required(
                        CONF_BLE_WRITE_CHAR,
                        default=options.get(CONF_BLE_WRITE_CHAR, DEFAULT_BLE_WRITE_CHAR),
                    ): vol.In([CHAR_WRITE_UUID, CHAR_WRITE_ALT_UUID]),
                    vol.Required(
                        CONF_BLE_WRITE_WITH_RESPONSE,
                        default=options.get(
                            CONF_BLE_WRITE_WITH_RESPONSE,
                            DEFAULT_BLE_WRITE_WITH_RESPONSE,
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_BLE_INIT_MESSAGE,
                        default=options.get(
                            CONF_BLE_INIT_MESSAGE,
                            json.dumps(DEFAULT_BLE_INIT_MESSAGE),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_BLE_APPEND_NEWLINE,
                        default=options.get(
                            CONF_BLE_APPEND_NEWLINE,
                            DEFAULT_BLE_APPEND_NEWLINE,
                        ),
                    ): bool,
                }
            )
        else:
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=update_seconds): int,
                    vol.Optional(
                        CONF_PATH,
                        default=options.get(
                            CONF_PATH,
                            self._entry.data.get(CONF_PATH, DEFAULT_WS_PATH),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_WS_INIT_MESSAGE,
                        default=options.get(
                            CONF_WS_INIT_MESSAGE,
                            json.dumps(DEFAULT_WS_INIT_MESSAGE),
                        ),
                    ): str,
                }
            )

        return self.async_show_form(step_id="init", data_schema=data_schema)


def _has_service_uuid(info: bluetooth.BluetoothServiceInfoBleak, uuid: str) -> bool:
    return uuid.lower() in {service.lower() for service in info.service_uuids}
