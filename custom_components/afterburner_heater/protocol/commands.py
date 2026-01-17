"""Command builders for Afterburner Heater protocol.

This module provides type-safe command builders for the heater protocol.
"""

from __future__ import annotations

from typing import Any, Literal


# Command type aliases for documentation
RefreshCommand = dict[Literal["Refresh"], Literal[1]]
RunCommand = dict[Literal["Run"], Literal["heat", "off"]]


def build_command(key: str, value: Any) -> dict[str, Any]:
    """Build a generic command payload."""
    return {key: value}


def refresh_command() -> RefreshCommand:
    """Build a refresh/status request command."""
    return {"Refresh": 1}


def run_command(mode: Literal["heat", "off"]) -> RunCommand:
    """Build a run mode command.

    Args:
        mode: "heat" to start heating, "off" to stop
    """
    return {"Run": mode}


def cyclic_temp_command(temp_f: float) -> dict[str, float]:
    """Build a cyclic temperature setpoint command.

    Args:
        temp_f: Temperature in Fahrenheit
    """
    return {"CyclicTemp": temp_f}


def cyclic_on_command(temp_f: float) -> dict[str, float]:
    """Build a cyclic restart temperature command.

    Args:
        temp_f: Temperature in Fahrenheit at which heater restarts
    """
    return {"CyclicOn": temp_f}


def cyclic_off_command(temp_f: float) -> dict[str, float]:
    """Build a cyclic stop temperature command.

    Args:
        temp_f: Temperature in Fahrenheit at which heater stops
    """
    return {"CyclicOff": temp_f}


def cyclic_enabled_command(enabled: bool) -> dict[str, int]:
    """Build a cyclic mode enable/disable command.

    Args:
        enabled: True to enable cyclic mode, False to disable
    """
    return {"CyclicEnb": 1 if enabled else 0}


def frost_enable_command(enabled: bool) -> dict[str, int]:
    """Build a frost protection enable/disable command.

    Args:
        enabled: True to enable frost protection, False to disable
    """
    return {"FrostEnable": 1 if enabled else 0}


def frost_on_command(temp_f: float) -> dict[str, float]:
    """Build a frost protection activation temperature command.

    Args:
        temp_f: Temperature in Fahrenheit below which frost protection activates
    """
    return {"FrostOn": temp_f}


def frost_rise_command(temp_f: float) -> dict[str, float]:
    """Build a frost protection rise temperature command.

    Args:
        temp_f: Temperature rise in Fahrenheit for frost protection
    """
    return {"FrostRise": temp_f}


def frost_target_command(temp_f: float) -> dict[str, float]:
    """Build a frost protection target temperature command.

    Args:
        temp_f: Target temperature in Fahrenheit for frost protection
    """
    return {"FrostTarget": temp_f}


def thermostat_command(enabled: bool) -> dict[str, int]:
    """Build a thermostat mode enable/disable command.

    Args:
        enabled: True to enable thermostat mode, False to disable
    """
    return {"Thermostat": 1 if enabled else 0}


def thermostat_mode_command(
    mode: Literal["Deadband", "Standard", "Stop/Start", "Linear Hz"]
) -> dict[str, str]:
    """Build a thermostat mode selection command.

    Args:
        mode: Thermostat operating mode
    """
    return {"ThermostatMode": mode}


def fixed_demand_command(value: float | None) -> dict[str, float | None]:
    """Build a fixed demand command.

    Args:
        value: Fixed demand value (0.0-1.0), or None to disable
    """
    return {"FixedDemand": value}


def gpout1_command(state: bool) -> dict[str, int]:
    """Build a GP output 1 command.

    Args:
        state: True for on, False for off
    """
    return {"GPout1": 1 if state else 0}


def gpout2_command(state: bool) -> dict[str, int]:
    """Build a GP output 2 command.

    Args:
        state: True for on, False for off
    """
    return {"GPout2": 1 if state else 0}
