"""Number entities for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from typing import cast

from homeassistant.components.number import NumberEntity, NumberEntityDescription
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
        name="Cyclic Temperature",
    ),
    NumberEntityDescription(
        key="CyclicOn",
        name="Cyclic On Offset",
    ),
    NumberEntityDescription(
        key="CyclicOff",
        name="Cyclic Off Offset",
    ),
    NumberEntityDescription(
        key="FrostOn",
        name="Frost Start Temperature",
    ),
    NumberEntityDescription(
        key="FrostRise",
        name="Frost Rise",
    ),
    NumberEntityDescription(
        key="FrostTarget",
        name="Frost Target Temperature",
    ),
    NumberEntityDescription(
        key="FixedDemand",
        name="Set Power Demand",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Afterburner Heater numbers."""
    coordinator: AfterburnerCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities(
        AfterburnerNumber(coordinator, entry, description)
        for description in NUMBER_DESCRIPTIONS
    )


class AfterburnerNumber(CoordinatorEntity[AfterburnerCoordinator], NumberEntity):
    """Representation of an Afterburner Heater number."""

    _attr_has_entity_name = True
    _attr_native_step = 0.1

    def __init__(
        self,
        coordinator: AfterburnerCoordinator,
        entry,
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
