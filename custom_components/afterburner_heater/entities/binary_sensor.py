"""Binary sensor entities for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from typing import cast

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import AfterburnerCoordinator
from ..protocol import HeaterState, raw_bool

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="RunReq",
        name="Run Request",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:run",
    ),
    BinarySensorEntityDescription(
        key="FrostRun",
        name="Frost Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:snowflake",
    ),
    BinarySensorEntityDescription(
        key="FrostHold",
        name="Frost Hold",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:clock-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Afterburner Heater binary sensors."""
    coordinator: AfterburnerCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities(
        AfterburnerBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class AfterburnerBinarySensor(
    CoordinatorEntity[AfterburnerCoordinator], BinarySensorEntity
):
    """Representation of an Afterburner Heater binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AfterburnerCoordinator,
        entry,
        description: BinarySensorEntityDescription,
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
