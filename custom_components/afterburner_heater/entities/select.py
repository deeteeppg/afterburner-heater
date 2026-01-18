"""Select entities for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from typing import cast

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import AfterburnerCoordinator
from ..protocol import HeaterState

THERMOSTAT_MODE_OPTIONS = ["Standard", "Deadband", "Linear Hz", "Stop/Start"]
FROST_MODE_OPTIONS = ["Off", "Start/Stop", "System Thermostat", "Frost Thermostat"]

SELECT_DESCRIPTIONS: tuple[SelectEntityDescription, ...] = (
    SelectEntityDescription(
        key="ThermostatMode",
        translation_key="ThermostatMode",
        options=THERMOSTAT_MODE_OPTIONS,
    ),
    SelectEntityDescription(
        key="FrostMode",
        translation_key="FrostMode",
        options=FROST_MODE_OPTIONS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Afterburner Heater selects."""
    coordinator: AfterburnerCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        AfterburnerSelect(coordinator, entry, description)
        for description in SELECT_DESCRIPTIONS
    )


class AfterburnerSelect(CoordinatorEntity[AfterburnerCoordinator], SelectEntity):
    """Representation of an Afterburner Heater select."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AfterburnerCoordinator,
        entry: ConfigEntry,
        description: SelectEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}-{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Afterburner",
        )

    @property
    def current_option(self) -> str | None:
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return None
        value = state.raw.get(self.entity_description.key)
        return None if value is None else str(value)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator._api.async_send_json(
            {self.entity_description.key: option}
        )
