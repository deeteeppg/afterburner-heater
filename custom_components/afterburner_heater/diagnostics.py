"""Diagnostics support for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import redact

from .const import DOMAIN

_SENSITIVE_KEYS = {
    "mpasswd",
    "muser",
    "password",
    "passwd",
    "token",
    "access_token",
    "authorization",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data = entry.runtime_data
    coordinator = runtime_data.coordinator

    return {
        "entry": _redact_sensitive(dict(entry.data)),
        "options": _redact_sensitive(dict(entry.options)),
        "transport": runtime_data.transport,
        "ws_init_message": entry.options.get("ws_init_message"),
        "ble_init_message": entry.options.get("ble_init_message"),
        "ble_append_newline": entry.options.get("ble_append_newline"),
        "last_payload": _redact_sensitive(
            coordinator.data.raw if coordinator.data else {}
        ),
    }


def _redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and key.lower() in _SENSITIVE_KEYS:
                redacted[key] = redact.REDACTED
            else:
                redacted[key] = _redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    return value
