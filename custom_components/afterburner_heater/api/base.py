"""Afterburner Heater API base classes.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

MessageCallback = Callable[[dict[str, Any]], None]


class HeaterApi(ABC):
    """Abstract transport API."""

    def __init__(self, message_callback: MessageCallback) -> None:
        self._message_callback = message_callback

    @abstractmethod
    async def async_start(self) -> None:
        """Start the transport."""

    @abstractmethod
    async def async_stop(self) -> None:
        """Stop the transport."""

    @abstractmethod
    async def async_send_json(self, payload: dict[str, Any]) -> None:
        """Send a JSON payload to the heater."""

    async def async_request_refresh(self) -> None:
        """Optionally request a state refresh."""

    def _handle_message(self, payload: dict[str, Any]) -> None:
        """Invoke the registered message callback."""
        self._message_callback(payload)
