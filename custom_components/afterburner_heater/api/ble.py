"""BLE transport for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import async_timeout
from bleak import BleakClient, BleakError
from bleak_retry_connector import BleakError as BleakRetryError, establish_connection

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.core import HomeAssistant

from ..protocol import (
    CHAR_NOTIFY_UUID,
    CHAR_WRITE_ALT_UUID,
    CHAR_WRITE_UUID,
    DEFAULT_BLE_COMMAND_TIMEOUT,
    DEFAULT_BLE_CONNECT_TIMEOUT,
    JsonObjectStream,
)
from .base import HeaterApi, MessageCallback

_LOGGER = logging.getLogger(__name__)

_MAX_BACKOFF = 30
_REFRESH_DELAY = 0.2
_REFRESH_LOG_DELAY = 2.0


class BleHeaterApi(HeaterApi):
    """BLE transport implementation."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        write_char: str,
        write_with_response: bool,
        message_callback: MessageCallback,
        init_message: dict[str, Any] | None = None,
        append_newline: bool = False,
    ) -> None:
        super().__init__(message_callback)
        self._hass = hass
        self._address = address
        self._write_char = _format_uuid(write_char)
        self._write_with_response = write_with_response
        self._init_message = init_message
        self._append_newline = append_newline
        self._client: BleakClient | None = None
        self._connect_lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._disconnected_event = asyncio.Event()
        self._stream = JsonObjectStream()
        self._refresh_pending = False
        self._refresh_message_count = 0
        self._refresh_log_task: asyncio.Task | None = None

    async def async_start(self) -> None:
        """Start BLE background task."""
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def async_stop(self) -> None:
        """Stop BLE background task."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._disconnect()

    async def async_send_json(self, payload: dict[str, Any]) -> None:
        """Send JSON payload over BLE."""
        suffix = "\n" if self._append_newline else ""
        data = f"{json.dumps(payload)}{suffix}".encode("utf-8")
        async with self._connect_lock:
            if not self._client or not self._client.is_connected:
                await self._connect()
            if not self._client:
                raise BleakError("BLE client unavailable")
            async with async_timeout.timeout(DEFAULT_BLE_COMMAND_TIMEOUT):
                await self._client.write_gatt_char(
                    self._write_char, data, response=self._write_with_response
                )

    async def async_request_refresh(self) -> None:
        """Request a state refresh."""
        if not self._init_message:
            return
        self._hass.async_create_task(self._async_send_init_message())

    async def _async_send_init_message(self) -> None:
        try:
            await self.async_send_json(self._init_message)
            self._start_refresh_tracking()
            _LOGGER.debug("BLE init sent: %s", self._init_message)
        except (BleakError, BleakRetryError, asyncio.TimeoutError) as err:
            _LOGGER.debug("BLE init send failed: %s", err)

    async def _run(self) -> None:
        backoff = 1
        while not self._stop_event.is_set():
            try:
                await self._connect()
                await self._subscribe_and_listen()
                backoff = 1
            except (BleakError, BleakRetryError, asyncio.TimeoutError) as err:
                _LOGGER.debug("BLE transport error: %s", err)
                await self._disconnect()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF)
            except asyncio.CancelledError:
                break
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected BLE error: %s", err)
                await self._disconnect()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF)

    async def _connect(self) -> None:
        if self._client and self._client.is_connected:
            return
        ble_device = async_ble_device_from_address(self._hass, self._address)
        if not ble_device:
            raise BleakError(f"Device not found: {self._address}")
        async with async_timeout.timeout(DEFAULT_BLE_CONNECT_TIMEOUT):
            self._client = await establish_connection(
                BleakClient, ble_device, self._address
            )
        self._disconnected_event.clear()
        self._client.set_disconnected_callback(
            lambda _: self._disconnected_event.set()
        )

    async def _disconnect(self) -> None:
        if self._client:
            try:
                await self._client.disconnect()
            except BleakError as err:
                _LOGGER.debug("BLE disconnect error: %s", err)
            self._client = None
        self._refresh_pending = False
        if self._refresh_log_task:
            self._refresh_log_task.cancel()
            self._refresh_log_task = None

    async def _subscribe_and_listen(self) -> None:
        if not self._client:
            return

        def _handle_notify(_: int, payload: bytearray) -> None:
            text = payload.decode("utf-8", errors="replace")
            if not text:
                return
            for decoded in self._stream.feed(text):
                _log_payload(decoded)
                self._note_refresh_message()
                self._handle_message(decoded)

        async with async_timeout.timeout(DEFAULT_BLE_CONNECT_TIMEOUT):
            await self._client.start_notify(
                _format_uuid(CHAR_NOTIFY_UUID), _handle_notify
            )
        await asyncio.sleep(_REFRESH_DELAY)
        await self.async_request_refresh()
        try:
            stop_task = asyncio.create_task(self._stop_event.wait())
            disconnect_task = asyncio.create_task(self._disconnected_event.wait())
            done, pending = await asyncio.wait(
                {stop_task, disconnect_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
        finally:
            if self._client and self._client.is_connected:
                await self._client.stop_notify(_format_uuid(CHAR_NOTIFY_UUID))


    def _start_refresh_tracking(self) -> None:
        self._refresh_pending = True
        self._refresh_message_count = 0
        self._schedule_refresh_log()

    def _note_refresh_message(self) -> None:
        if not self._refresh_pending:
            return
        self._refresh_message_count += 1
        self._schedule_refresh_log()

    def _schedule_refresh_log(self) -> None:
        if self._refresh_log_task:
            self._refresh_log_task.cancel()
        self._refresh_log_task = self._hass.async_create_task(
            self._log_refresh_summary()
        )

    async def _log_refresh_summary(self) -> None:
        try:
            await asyncio.sleep(_REFRESH_LOG_DELAY)
        except asyncio.CancelledError:
            return
        _LOGGER.debug(
            "BLE refresh dump messages received: %d", self._refresh_message_count
        )
        self._refresh_pending = False


def _format_uuid(uuid: str) -> str:
    normalized = uuid.lower()
    if len(normalized) == 4:
        return f"0000{normalized}-0000-1000-8000-00805f9b34fb"
    return normalized


def resolve_write_uuid(write_char: str) -> str:
    """Resolve write characteristic UUID."""
    if write_char.upper() == CHAR_WRITE_ALT_UUID:
        return CHAR_WRITE_ALT_UUID
    return CHAR_WRITE_UUID


def _log_payload(payload: dict[str, Any]) -> None:
    _LOGGER.debug("BLE payload keys: %d", len(payload))
