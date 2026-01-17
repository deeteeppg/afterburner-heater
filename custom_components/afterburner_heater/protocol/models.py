"""Afterburner Heater models and parsing helpers.

Shared protocol models for state representation and payload normalization.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass
class HeaterState:
    """Normalized heater state."""

    temperature: float | None = None
    humidity: float | None = None
    voltage: float | None = None
    power: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    normalized: dict[str, Any] = field(default_factory=dict)

    def merge_payload(self, payload: dict[str, Any]) -> "HeaterState":
        """Merge a new payload into the state, returning a new HeaterState.

        This method is immutable - it returns a new HeaterState instance
        rather than modifying the existing one, preventing race conditions
        when concurrent async tasks access the state.
        """
        normalized = normalize_payload(payload)
        parsed = parse_message(normalized)
        new_raw = {**self.raw, **payload}
        new_normalized = {**self.normalized, **normalized}

        # Debug: log power and GPIO keys
        debug_keys = ("Run", "RunState", "Power", "GPout1", "GPout2")
        found_keys = {k: v for k, v in payload.items() if k in debug_keys}
        if found_keys:
            norm_vals = {k: normalized.get(k) for k in found_keys}
            _LOGGER.debug(
                "State keys - raw: %s, normalized: %s",
                found_keys, norm_vals
            )

        return HeaterState(
            temperature=parsed.temperature if parsed.temperature is not None else self.temperature,
            humidity=parsed.humidity if parsed.humidity is not None else self.humidity,
            voltage=parsed.voltage if parsed.voltage is not None else self.voltage,
            power=parsed.power if parsed.power is not None else self.power,
            raw=new_raw,
            normalized=new_normalized,
        )

    def value(self, key: str) -> Any:
        """Return a normalized value if available, otherwise raw."""
        if key in self.normalized:
            return self.normalized[key]
        return self.raw.get(key)


def parse_message(payload: dict[str, Any]) -> HeaterState:
    """Parse a raw payload into a HeaterState."""
    return HeaterState(
        temperature=_parse_float(
            payload,
            [
                "Temperature",
                "temperature",
                "temp",
                "TempCurrent",
                "Temp1Current",
                "Temp4Current",
            ],
        ),
        humidity=_parse_float(payload, ["Humidity", "humidity", "hum"]),
        voltage=_parse_float(
            payload, ["Voltage", "voltage", "v", "InputVoltage", "SystemVoltage"]
        ),
        power=_parse_bool(payload, ["Power", "power", "on", "Run", "RunState"]),
        raw=dict(payload),
        normalized=dict(payload),
    )


def state_text_from_raw(raw: dict[str, Any]) -> str | None:
    """Pick a human-friendly state string from payloads."""
    for key in ("State", "Status", "Mode", "RunString", "ThermostatMode"):
        value = raw.get(key)
        if value is not None:
            return str(value)
    return None


def raw_value(raw: dict[str, Any], keys: list[str]) -> Any:
    """Return the first matching raw value for the provided keys."""
    for key in keys:
        if key in raw:
            return raw[key]
    return None


def raw_bool(raw: dict[str, Any], keys: list[str]) -> bool | None:
    """Return a parsed boolean for the first matching raw key."""
    for key in keys:
        if key not in raw:
            continue
        return _coerce_bool(raw[key])
    return None


TEMPERATURE_KEYS = {
    "Temperature",
    "temperature",
    "temp",
    "TempCurrent",
    "TempDesired",
    "TempBody",
    "Temp1Current",
    "Temp4Current",
    "FrostRise",
    "FrostOn",
    "FrostTarget",
    "CyclicTemp",
    "CyclicOn",
    "CyclicOff",
    "ThermMin",
    "ThermMax",
    "ThermostatOvertemp",
    "ThermostatUndertemp",
    "AbsCyclicOn",
    "AbsCyclicOff",
}

BOOL_KEYS = {
    "Power",
    "power",
    "on",
    "Run",
    "RunState",
    "CyclicEnb",
    "FrostEnable",
    "Thermostat",
    "GPout1",
    "GPout2",
    "GPin1",
    "GPin2",
    "RunReq",
    "FrostRun",
    "FrostHold",
}

INT_KEYS = {"FanRPM"}

FLOAT_KEYS = {
    "Humidity",
    "humidity",
    "hum",
    "Voltage",
    "voltage",
    "v",
    "InputVoltage",
    "SystemVoltage",
    "GlowVoltage",
    "GlowCurrent",
    "PumpActual",
    "PumpFixed",
    "FuelUsage",
    "TotalFuelUsage",
    "FuelRate",
    "Altitude",
    "GPanlg",
    "Pressure",
    "FixedDemand",
    "SysTotalFuel",
}

STR_KEYS = {
    "FuelAlarm",
    "RunString",
    "ErrorString",
    "ThermostatMode",
    "FrostMode",
    "GPmodeIn1",
    "GPmodeIn2",
    "GPmodeOut1",
    "GPmodeOut2",
}


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize raw payload types and units for HA."""
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        if key in TEMPERATURE_KEYS:
            normalized[key] = _coerce_temperature(value)
        elif key in BOOL_KEYS:
            normalized[key] = _coerce_bool(value)
        elif key in INT_KEYS:
            normalized[key] = _coerce_int(value)
        elif key in FLOAT_KEYS:
            normalized[key] = _coerce_float(value)
        elif key in STR_KEYS:
            normalized[key] = _coerce_str(value)
        else:
            normalized[key] = value

    abs_cyclic_on = normalized.get("AbsCyclicOn")
    abs_cyclic_present = False
    if isinstance(abs_cyclic_on, (int, float)):
        normalized["CyclicRestartTemp"] = abs_cyclic_on
        abs_cyclic_present = True

    abs_cyclic_off = normalized.get("AbsCyclicOff")
    if isinstance(abs_cyclic_off, (int, float)):
        normalized["CyclicStopTemp"] = abs_cyclic_off
        abs_cyclic_present = True

    therm_min = normalized.get("ThermMin")
    if isinstance(therm_min, (int, float)) and not abs_cyclic_present:
        normalized["CyclicRestartTemp"] = therm_min
        normalized["CyclicStopTemp"] = therm_min

    if (
        "CyclicRestartTemp" not in normalized
        or "CyclicStopTemp" not in normalized
    ):
        cyclic_temp = normalized.get("CyclicTemp")
        if isinstance(cyclic_temp, (int, float)):
            normalized.setdefault("CyclicRestartTemp", cyclic_temp)
            normalized.setdefault("CyclicStopTemp", cyclic_temp)

    thermo_over = normalized.get("ThermostatOvertemp")
    if isinstance(thermo_over, (int, float)):
        normalized["CyclicOff"] = thermo_over

    thermo_under = normalized.get("ThermostatUndertemp")
    if isinstance(thermo_under, (int, float)):
        normalized["CyclicOn"] = thermo_under

    fuel_alarm = normalized.get("FuelAlarm")
    if fuel_alarm is not None:
        try:
            fuel_code = int(float(fuel_alarm))
        except (TypeError, ValueError):
            normalized["FuelAlarm"] = _coerce_str(fuel_alarm)
        else:
            normalized["FuelAlarm"] = "0: OK" if fuel_code == 0 else str(fuel_code)

    sys_total_fuel = normalized.get("SysTotalFuel")
    if isinstance(sys_total_fuel, (int, float)):
        normalized.setdefault("FuelUsage", sys_total_fuel)
        normalized.setdefault("TotalFuelUsage", sys_total_fuel)

    return normalized


def _coerce_temperature(value: Any) -> float | None:
    return _coerce_float(value)


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _parse_float(payload: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        if key not in payload:
            continue
        value = payload[key]
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return None


def _parse_bool(payload: dict[str, Any], keys: list[str]) -> bool | None:
    for key in keys:
        if key not in payload:
            continue
        return _coerce_bool(payload[key])
    return None


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "on", "1", "yes", "heat", "heating", "running"}:
            return True
        if normalized in {"false", "off", "0", "no", "cooling", "stopped", "idle", "standby"}:
            return False
    return None
