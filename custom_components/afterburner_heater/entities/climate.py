"""Climate entity for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from typing import Any, cast

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import AfterburnerCoordinator
from ..protocol import HeaterState

# Thermostat mode options from the heater
PRESET_MODES = ["Standard", "Deadband", "Linear Hz", "Stop/Start"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Afterburner Heater climate."""
    coordinator: AfterburnerCoordinator = entry.runtime_data.coordinator
    async_add_entities([AfterburnerClimate(coordinator, entry)])


class AfterburnerClimate(CoordinatorEntity[AfterburnerCoordinator], ClimateEntity):
    """Climate entity for Afterburner Heater."""

    _attr_has_entity_name = True
    _attr_translation_key = "heater"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = PRESET_MODES
    _attr_min_temp = 0
    _attr_max_temp = 40
    _attr_target_temperature_step = 0.5

    def __init__(
        self,
        coordinator: AfterburnerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}-climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Afterburner",
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return None
        # Try multiple temperature keys in order of preference
        for key in ("Temp1Current", "TempCurrent", "Temperature", "Temp4Current"):
            if key in state.raw:
                try:
                    return float(state.raw[key])
                except (TypeError, ValueError):
                    continue
        return state.temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return None
        # CyclicTemp is the setpoint, or try TempDesired
        for key in ("CyclicTemp", "TempDesired"):
            if key in state.raw:
                try:
                    return float(state.raw[key])
                except (TypeError, ValueError):
                    continue
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return HVACMode.OFF

        # Check RunString first for most accurate state
        run_string = state.raw.get("RunString", "")
        if isinstance(run_string, str):
            run_lower = run_string.lower()
            # Cooling/stopping means heater is off (not actively heating)
            if "cool" in run_lower or "stop" in run_lower or "off" in run_lower:
                return HVACMode.OFF
            if "heat" in run_lower or "run" in run_lower:
                return HVACMode.HEAT

        # Fall back to power state (now recognizes cooling as False)
        if state.power is True:
            return HVACMode.HEAT
        if state.power is False:
            return HVACMode.OFF

        # Check Run key directly as last resort
        run_state = state.raw.get("Run") or state.raw.get("RunState")
        if run_state:
            if isinstance(run_state, str):
                run_lower = run_state.lower()
                if run_lower in {"heat", "heating", "on", "running"}:
                    return HVACMode.HEAT
                if run_lower in {"off", "cooling", "stopped", "idle"}:
                    return HVACMode.OFF
            if isinstance(run_state, (int, float)):
                return HVACMode.HEAT if run_state else HVACMode.OFF

        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return current HVAC action."""
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return None

        # Check RunString for detailed state
        run_string = state.raw.get("RunString", "")
        if isinstance(run_string, str):
            run_lower = run_string.lower()
            if "heat" in run_lower or "running" in run_lower:
                return HVACAction.HEATING
            if "cool" in run_lower:
                # Cooling down after shutdown - fan still running
                return HVACAction.IDLE
            if "idle" in run_lower or "standby" in run_lower:
                return HVACAction.IDLE
            if "off" in run_lower or "stop" in run_lower:
                return HVACAction.OFF

        # Fall back to hvac_mode
        if self.hvac_mode == HVACMode.HEAT:
            return HVACAction.HEATING
        return HVACAction.OFF

    @property
    def preset_mode(self) -> str | None:
        """Return current preset mode (thermostat mode)."""
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return None
        mode = state.raw.get("ThermostatMode")
        if mode and str(mode) in PRESET_MODES:
            return str(mode)
        return None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        if hvac_mode == HVACMode.HEAT:
            await self.coordinator._api.async_send_json({"Run": "heat"})
        else:
            await self.coordinator._api.async_send_json({"Run": "off"})

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.coordinator._api.async_send_json({"CyclicTemp": temperature})

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode (thermostat mode)."""
        if preset_mode in PRESET_MODES:
            await self.coordinator._api.async_send_json({"ThermostatMode": preset_mode})
