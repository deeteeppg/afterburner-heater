"""WebSocket transport for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..protocol import DEFAULT_WS_PATH, DEFAULT_WS_COMMAND_TIMEOUT
from .base import HeaterApi, MessageCallback

_LOGGER = logging.getLogger(__name__)

_MAX_BACKOFF = 30
_WS_CONNECT_TIMEOUT = 10
_HEARTBEAT_INTERVAL = 30  # seconds
_HEARTBEAT_TIMEOUT = 10  # seconds to wait for pong


class WebSocketHeaterApi(HeaterApi):
    """WebSocket transport implementation."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int | None,
        path: str | None,
        message_callback: MessageCallback,
        token: str | None = None,
        init_message: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message_callback)
        self._hass = hass
        self._host = host
        self._port = port
        self._path = _normalize_path(path)
        self._token = token
        self._init_message = init_message
        self._session = async_get_clientsession(hass)
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._send_lock = asyncio.Lock()

    async def async_start(self) -> None:
        """Start WebSocket background task."""
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def async_stop(self) -> None:
        """Stop WebSocket background task."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._disconnect()

    async def async_send_json(self, payload: dict[str, Any]) -> None:
        """Send JSON payload over WebSocket."""
        async with self._send_lock:
            if not self._ws or self._ws.closed:
                raise ConnectionError("WebSocket not connected")
            async with async_timeout.timeout(DEFAULT_WS_COMMAND_TIMEOUT):
                await self._ws.send_str(json.dumps(payload))

    async def async_request_refresh(self) -> None:
        """Optionally request a state refresh."""
        if not self._ws or self._ws.closed:
            return
        if self._init_message:
            await self._ws.send_json(self._init_message)
            _LOGGER.debug("WebSocket refresh sent: %s", self._init_message)
        else:
            _LOGGER.debug("WebSocket refresh requested (no init message configured)")

    async def _run(self) -> None:
        backoff = 1
        while not self._stop_event.is_set():
            try:
                await self._connect()
                await self._listen()
                backoff = 1
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                _LOGGER.debug("WebSocket transport error: %s", err)
                await self._disconnect()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF)
            except asyncio.CancelledError:
                break
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected WebSocket error: %s", err)
                await self._disconnect()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF)

    async def _connect(self) -> None:
        if self._ws and not self._ws.closed:
            return
        url = _build_ws_url(self._host, self._port, self._path)
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        async with async_timeout.timeout(_WS_CONNECT_TIMEOUT):
            self._ws = await self._session.ws_connect(url, headers=headers)
        if self._init_message:
            await self._ws.send_json(self._init_message)
            _LOGGER.debug("WebSocket init sent: %s", self._init_message)

    async def _disconnect(self) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.close()
        self._ws = None

    async def _listen(self) -> None:
        if not self._ws:
            return

        async def _heartbeat() -> None:
            """Send periodic pings to keep connection alive."""
            while self._ws and not self._ws.closed:
                try:
                    await asyncio.sleep(_HEARTBEAT_INTERVAL)
                    if self._ws and not self._ws.closed:
                        async with async_timeout.timeout(_HEARTBEAT_TIMEOUT):
                            await self._ws.ping()
                            _LOGGER.debug("WebSocket heartbeat ping sent")
                except asyncio.TimeoutError:
                    _LOGGER.warning("WebSocket heartbeat timeout, closing connection")
                    if self._ws and not self._ws.closed:
                        await self._ws.close()
                    break
                except asyncio.CancelledError:
                    break
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("WebSocket heartbeat error: %s", err)
                    break

        heartbeat_task = asyncio.create_task(_heartbeat())
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    decoded = _decode_payload(msg.data)
                    if decoded is not None:
                        _log_payload(decoded)
                        self._handle_message(decoded)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.debug("WebSocket error: %s", self._ws.exception())
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
                elif msg.type == aiohttp.WSMsgType.PONG:
                    _LOGGER.debug("WebSocket pong received")
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass


def _decode_payload(data: str) -> dict[str, Any] | None:
    try:
        return json.loads(data)
    except json.JSONDecodeError as err:
        _LOGGER.debug("Invalid JSON payload from WebSocket: %s", err)
        return None


def _normalize_path(path: str | None) -> str:
    if not path:
        return DEFAULT_WS_PATH
    if not path.startswith("/"):
        return f"/{path}"
    return path


def _build_ws_url(host: str, port: int | None, path: str) -> str:
    if port is None:
        # TODO: Confirm default port selection for WebSocket transport.
        return f"ws://{host}{path}"
    return f"ws://{host}:{port}{path}"


def _log_payload(payload: dict[str, Any]) -> None:
    keys = list(payload.keys())
    if len(keys) > 10:
        _LOGGER.debug("WebSocket payload keys (%d): %s", len(keys), keys)
    else:
        _LOGGER.debug("WebSocket payload: %s", payload)
