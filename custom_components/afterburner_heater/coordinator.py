"""Coordinator for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api.base import HeaterApi
from .protocol import HeaterState

_LOGGER = logging.getLogger(__name__)

# Number of latency samples to keep for averaging
_LATENCY_WINDOW_SIZE = 10


@dataclass
class TransportHealth:
    """Track transport health and latency statistics."""

    message_count: int = 0
    last_message_time: float | None = None
    last_refresh_time: float | None = None
    refresh_latencies: deque = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.refresh_latencies is None:
            self.refresh_latencies = deque(maxlen=_LATENCY_WINDOW_SIZE)

    @property
    def avg_latency_ms(self) -> float | None:
        """Average refresh latency in milliseconds."""
        if not self.refresh_latencies:
            return None
        return sum(self.refresh_latencies) / len(self.refresh_latencies)

    @property
    def is_stale(self) -> bool:
        """Check if transport hasn't received messages recently (>2 poll intervals)."""
        if self.last_message_time is None:
            return True
        return (time.monotonic() - self.last_message_time) > 120  # 2 minutes


class AfterburnerCoordinator(DataUpdateCoordinator[HeaterState]):
    """Coordinator for push/poll updates."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass,
        entry: ConfigEntry,
        api: HeaterApi,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            update_interval=update_interval,
        )
        self.config_entry = entry
        self._api = api
        self._state = HeaterState()
        self._health = TransportHealth()

    @property
    def health(self) -> TransportHealth:
        """Return transport health statistics."""
        return self._health

    async def async_start(self) -> None:
        """Start the transport."""
        await self._api.async_start()

    async def async_stop(self) -> None:
        """Stop the transport."""
        await self._api.async_stop()

    def handle_message(self, payload: dict) -> None:
        """Handle new payloads from the transport."""
        now = time.monotonic()
        self._health.message_count += 1
        self._health.last_message_time = now

        # Track refresh latency if we're waiting for a refresh response
        if self._health.last_refresh_time is not None:
            latency_ms = (now - self._health.last_refresh_time) * 1000
            self._health.refresh_latencies.append(latency_ms)
            self._health.last_refresh_time = None
            _LOGGER.debug(
                "Refresh latency: %.1fms (avg: %.1fms over %d samples)",
                latency_ms,
                self._health.avg_latency_ms,
                len(self._health.refresh_latencies),
            )

        self._state = self._state.merge_payload(payload)
        self.async_set_updated_data(self._state)

    async def _async_update_data(self) -> HeaterState:
        # Track when we send the refresh request for latency measurement
        self._health.last_refresh_time = time.monotonic()
        await self._api.async_request_refresh()
        return self._state
