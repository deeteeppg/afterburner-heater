"""Switch entities for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from typing import Any, cast

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import AfterburnerCoordinator
from ..protocol import HeaterState, raw_bool


SWITCH_DESCRIPTIONS: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="CyclicEnb",
        translation_key="CyclicEnb",
    ),
    SwitchEntityDescription(
        key="FrostEnable",
        translation_key="FrostEnable",
    ),
    SwitchEntityDescription(
        key="Thermostat",
        translation_key="Thermostat",
    ),
    SwitchEntityDescription(
        key="GPout1",
        translation_key="GPout1",
    ),
    SwitchEntityDescription(
        key="GPout2",
        translation_key="GPout2",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Afterburner Heater switches."""
    coordinator: AfterburnerCoordinator = entry.runtime_data.coordinator
    entities: list[SwitchEntity] = [AfterburnerPowerSwitch(coordinator, entry)]
    entities.extend(
        AfterburnerCommandSwitch(coordinator, entry, description)
        for description in SWITCH_DESCRIPTIONS
    )
    async_add_entities(entities)


class AfterburnerPowerSwitch(
    CoordinatorEntity[AfterburnerCoordinator], SwitchEntity
):
    """Representation of the Afterburner Heater power switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "power"

    def __init__(self, coordinator: AfterburnerCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}-power"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Afterburner",
        )

    @property
    def available(self) -> bool:
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return False
        return state.power is not None or "Power" in state.raw or "Run" in state.raw

    @property
    def is_on(self) -> bool | None:
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return None
        return state.power

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator._api.async_send_json({"Run": "heat"})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator._api.async_send_json({"Run": "off"})


class AfterburnerCommandSwitch(
    CoordinatorEntity[AfterburnerCoordinator], SwitchEntity
):
    """Representation of a command-backed switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AfterburnerCoordinator,
        entry: ConfigEntry,
        description: SwitchEntityDescription,
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
    def is_on(self) -> bool | None:
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return None
        return raw_bool(state.raw, [self.entity_description.key])

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator._api.async_send_json(
            {self.entity_description.key: 1}
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator._api.async_send_json(
            {self.entity_description.key: 0}
        )
