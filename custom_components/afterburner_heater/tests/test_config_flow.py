"""Tests for the Afterburner Heater config flow."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.afterburner_heater.config_flow import AfterburnerConfigFlow
from custom_components.afterburner_heater.const import (
    CONF_TRANSPORT,
    DEFAULT_WS_PATH,
    DEFAULT_WS_PORT,
    DOMAIN,
    TRANSPORT_BLE,
    TRANSPORT_WEBSOCKET,
)

pytestmark = pytest.mark.asyncio


async def test_user_step_shows_transport_selection(hass: HomeAssistant) -> None:
    """Test that the user step shows transport selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert CONF_TRANSPORT in result["data_schema"].schema


async def test_user_step_selects_ble(
    hass: HomeAssistant,
    mock_no_bluetooth_discovery: MagicMock,
) -> None:
    """Test selecting BLE transport goes to BLE step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_BLE},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "ble"


async def test_user_step_selects_websocket(hass: HomeAssistant) -> None:
    """Test selecting WebSocket transport goes to WebSocket step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_WEBSOCKET},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "websocket"


async def test_ble_step_with_discovered_devices(
    hass: HomeAssistant,
    mock_bluetooth_discovery: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test BLE step with discovered devices."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_BLE},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "ble"

    # Select the discovered device
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"address": "AA:BB:CC:DD:EE:FF"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Afterburner-1234"
    assert result["data"]["transport"] == TRANSPORT_BLE
    assert result["data"]["address"] == "AA:BB:CC:DD:EE:FF"


async def test_ble_step_with_manual_address(
    hass: HomeAssistant,
    mock_bluetooth_discovery: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test BLE step with manual address entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_BLE},
    )

    # Use manual address instead of discovered device
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"manual_address": "11:22:33:44:55:66"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["address"] == "11:22:33:44:55:66"


async def test_ble_step_no_devices_manual_entry(
    hass: HomeAssistant,
    mock_no_bluetooth_discovery: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test BLE step with no discovered devices requires manual entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_BLE},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "ble"

    # Enter manual address
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"address": "AA:BB:CC:DD:EE:FF"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY


async def test_ble_step_invalid_address_error(
    hass: HomeAssistant,
    mock_no_bluetooth_discovery: MagicMock,
) -> None:
    """Test BLE step shows error for invalid address."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_BLE},
    )

    # Submit empty address
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"address": ""},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_address"


async def test_websocket_step_success(
    hass: HomeAssistant,
    mock_websocket_connect: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test successful WebSocket configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_WEBSOCKET},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "websocket"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "192.168.1.100",
            "port": DEFAULT_WS_PORT,
            "path": DEFAULT_WS_PATH,
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Afterburner 192.168.1.100"
    assert result["data"]["transport"] == TRANSPORT_WEBSOCKET
    assert result["data"]["host"] == "192.168.1.100"
    assert result["data"]["port"] == DEFAULT_WS_PORT


async def test_websocket_step_connection_failed(
    hass: HomeAssistant,
    mock_websocket_connect_fail: AsyncMock,
) -> None:
    """Test WebSocket configuration fails with unreachable host."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_WEBSOCKET},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "invalid-host",
            "port": DEFAULT_WS_PORT,
            "path": DEFAULT_WS_PATH,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_websocket_step_with_token(
    hass: HomeAssistant,
    mock_websocket_connect: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test WebSocket configuration with access token."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_WEBSOCKET},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "192.168.1.100",
            "port": DEFAULT_WS_PORT,
            "path": DEFAULT_WS_PATH,
            "access_token": "secret-token",
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["access_token"] == "secret-token"


async def test_ble_duplicate_entry_aborted(
    hass: HomeAssistant,
    mock_bluetooth_discovery: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test BLE duplicate entry is aborted."""
    # Create first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_BLE},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"address": "AA:BB:CC:DD:EE:FF"},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Try to create duplicate entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_BLE},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"address": "AA:BB:CC:DD:EE:FF"},
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_websocket_duplicate_entry_aborted(
    hass: HomeAssistant,
    mock_websocket_connect: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test WebSocket duplicate entry is aborted."""
    # Create first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_WEBSOCKET},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "192.168.1.100",
            "port": DEFAULT_WS_PORT,
            "path": DEFAULT_WS_PATH,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Try to create duplicate entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRANSPORT: TRANSPORT_WEBSOCKET},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "192.168.1.100",
            "port": DEFAULT_WS_PORT,
            "path": DEFAULT_WS_PATH,
        },
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_not_supported(hass: HomeAssistant) -> None:
    """Test reauth is not supported."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH},
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_not_supported"


async def test_options_flow_ble(
    hass: HomeAssistant,
    mock_ble_config_entry_data: dict[str, Any],
) -> None:
    """Test options flow for BLE transport."""
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Test Afterburner BLE",
        data=mock_ble_config_entry_data,
        source=config_entries.SOURCE_USER,
        unique_id="ble_AA:BB:CC:DD:EE:FF",
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Verify BLE-specific options are in the schema
    schema_keys = [str(key) for key in result["data_schema"].schema.keys()]
    assert "scan_interval" in str(schema_keys)
    assert "ble_write_char" in str(schema_keys)


async def test_options_flow_websocket(
    hass: HomeAssistant,
    mock_ws_config_entry_data: dict[str, Any],
) -> None:
    """Test options flow for WebSocket transport."""
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Test Afterburner WS",
        data=mock_ws_config_entry_data,
        source=config_entries.SOURCE_USER,
        unique_id="ws_192.168.1.100:81",
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Verify WebSocket-specific options are in the schema
    schema_keys = [str(key) for key in result["data_schema"].schema.keys()]
    assert "scan_interval" in str(schema_keys)
    assert "path" in str(schema_keys)


async def test_options_flow_save(
    hass: HomeAssistant,
    mock_ws_config_entry_data: dict[str, Any],
) -> None:
    """Test options flow saves options."""
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Test Afterburner WS",
        data=mock_ws_config_entry_data,
        source=config_entries.SOURCE_USER,
        unique_id="ws_192.168.1.100:81",
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "scan_interval": 120,
            "path": "/custom",
            "ws_init_message": '{"Refresh": 1}',
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["scan_interval"] == 120
    assert result["data"]["path"] == "/custom"
