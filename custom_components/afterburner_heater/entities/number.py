"""Number entities for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from typing import cast

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import AfterburnerCoordinator
from ..protocol import HeaterState

NUMBER_DESCRIPTIONS: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key="CyclicTemp",
        translation_key="CyclicTemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=-20,
        native_max_value=40,
        native_step=0.5,
    ),
    NumberEntityDescription(
        key="CyclicOn",
        translation_key="CyclicOn",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=-10,
        native_max_value=10,
        native_step=0.5,
    ),
    NumberEntityDescription(
        key="CyclicOff",
        translation_key="CyclicOff",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=-10,
        native_max_value=10,
        native_step=0.5,
    ),
    NumberEntityDescription(
        key="FrostOn",
        translation_key="FrostOn",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=-20,
        native_max_value=10,
        native_step=0.5,
    ),
    NumberEntityDescription(
        key="FrostRise",
        translation_key="FrostRise",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=0,
        native_max_value=20,
        native_step=0.5,
    ),
    NumberEntityDescription(
        key="FrostTarget",
        translation_key="FrostTarget",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=-10,
        native_max_value=20,
        native_step=0.5,
    ),
    NumberEntityDescription(
        key="FixedDemand",
        translation_key="FixedDemand",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Afterburner Heater numbers."""
    coordinator: AfterburnerCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        AfterburnerNumber(coordinator, entry, description)
        for description in NUMBER_DESCRIPTIONS
    )


class AfterburnerNumber(CoordinatorEntity[AfterburnerCoordinator], NumberEntity):
    """Representation of an Afterburner Heater number."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AfterburnerCoordinator,
        entry: ConfigEntry,
        description: NumberEntityDescription,
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
    def native_value(self) -> float | None:
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return None
        value = state.raw.get(self.entity_description.key)
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator._api.async_send_json(
            {self.entity_description.key: value}
        )
