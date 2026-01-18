"""Fixtures for Afterburner Heater tests."""
from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant

from custom_components.afterburner_heater.const import (
    DOMAIN,
    SERVICE_UUID,
    TRANSPORT_BLE,
    TRANSPORT_WEBSOCKET,
)


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.afterburner_heater.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def mock_bluetooth_service_info() -> BluetoothServiceInfoBleak:
    """Return a mock BluetoothServiceInfoBleak for testing."""
    return BluetoothServiceInfoBleak(
        name="Afterburner-1234",
        address="AA:BB:CC:DD:EE:FF",
        rssi=-50,
        manufacturer_data={},
        service_data={},
        service_uuids=[SERVICE_UUID.lower()],
        source="local",
        device=MagicMock(),
        advertisement=MagicMock(),
        connectable=True,
        time=0,
        tx_power=None,
    )


@pytest.fixture
def mock_bluetooth_discovery(
    mock_bluetooth_service_info: BluetoothServiceInfoBleak,
) -> Generator[MagicMock, None, None]:
    """Mock bluetooth discovery to return test devices."""
    with patch(
        "homeassistant.components.bluetooth.async_discovered_service_info",
        return_value=[mock_bluetooth_service_info],
    ) as mock_discovery:
        yield mock_discovery


@pytest.fixture
def mock_no_bluetooth_discovery() -> Generator[MagicMock, None, None]:
    """Mock bluetooth discovery to return no devices."""
    with patch(
        "homeassistant.components.bluetooth.async_discovered_service_info",
        return_value=[],
    ) as mock_discovery:
        yield mock_discovery


@pytest.fixture
def mock_websocket_connect() -> Generator[AsyncMock, None, None]:
    """Mock successful WebSocket connection."""
    mock_ws = AsyncMock()
    mock_ws.close = AsyncMock()
    mock_ws.closed = False

    with patch(
        "custom_components.afterburner_heater.config_flow.async_get_clientsession"
    ) as mock_session_getter:
        mock_session = AsyncMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)

        # Make ws_connect work as an async context manager
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session.ws_connect.return_value = mock_cm

        mock_session_getter.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_websocket_connect_fail() -> Generator[AsyncMock, None, None]:
    """Mock failed WebSocket connection."""
    with patch(
        "custom_components.afterburner_heater.config_flow.async_get_clientsession"
    ) as mock_session_getter:
        mock_session = AsyncMock()
        mock_session.ws_connect = AsyncMock(side_effect=Exception("Connection refused"))
        mock_session_getter.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_ble_config_entry_data() -> dict[str, Any]:
    """Return mock BLE config entry data."""
    return {
        "transport": TRANSPORT_BLE,
        "address": "AA:BB:CC:DD:EE:FF",
    }


@pytest.fixture
def mock_ws_config_entry_data() -> dict[str, Any]:
    """Return mock WebSocket config entry data."""
    return {
        "transport": TRANSPORT_WEBSOCKET,
        "host": "192.168.1.100",
        "port": 81,
        "path": "/",
        "access_token": None,
    }
