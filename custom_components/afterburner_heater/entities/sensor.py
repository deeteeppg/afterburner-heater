"""Sensor entities for Afterburner Heater.

Generated with ha-integration@aurora-smart-home v1.0.0
https://github.com/tonylofgren/aurora-smart-home
"""
from __future__ import annotations

from typing import cast

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import AfterburnerCoordinator
from ..protocol import HeaterState, state_text_from_raw

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    SensorEntityDescription(
        key="temperature",
        name="Temperature",
        # TODO: Confirm temperature unit from device payload.
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="voltage",
        name="Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SensorEntityDescription(
        key="state_text",
        name="State",
    ),
    SensorEntityDescription(
        key="TempCurrent",
        name="Actual Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="TempDesired",
        name="Desired Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="TempBody",
        name="Heater Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="Temp1Current",
        name="Sensor Thermostat",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="Temp4Current",
        name="Sensor BME280",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="InputVoltage",
        name="Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SensorEntityDescription(
        key="SystemVoltage",
        name="System Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SensorEntityDescription(
        key="GlowVoltage",
        name="Glow Plug Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SensorEntityDescription(
        key="GlowCurrent",
        name="Glow Plug Current",
        native_unit_of_measurement="A",
        device_class=SensorDeviceClass.CURRENT,
    ),
    SensorEntityDescription(
        key="FanRPM",
        name="Fan Speed",
        native_unit_of_measurement="RPM",
    ),
    SensorEntityDescription(
        key="PumpActual",
        name="Actual Pump Speed",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
    ),
    SensorEntityDescription(
        key="PumpFixed",
        name="Desired Pump Speed",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
    ),
    SensorEntityDescription(
        key="FuelUsage",
        name="Fuel Used",
        # TODO: Confirm fuel units and map to unit of volume.
        native_unit_of_measurement=None,
    ),
    SensorEntityDescription(
        key="TotalFuelUsage",
        name="Total Fuel Used",
        # TODO: Confirm fuel units and map to unit of volume.
        native_unit_of_measurement=None,
    ),
    SensorEntityDescription(
        key="FuelRate",
        name="Fuel Rate",
        # TODO: Confirm fuel rate units.
        native_unit_of_measurement=None,
    ),
    SensorEntityDescription(
        key="FrostRise",
        name="Frost Rise",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="Altitude",
        name="Altitude",
        native_unit_of_measurement="m",
    ),
    SensorEntityDescription(
        key="FuelAlarm",
        name="Fuel Status",
    ),
    SensorEntityDescription(
        key="RunString",
        name="Heater State",
    ),
    SensorEntityDescription(
        key="ErrorString",
        name="Error State",
    ),
    SensorEntityDescription(
        key="GPanlg",
        name="Analogue Input",
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(
        key="Pressure",
        name="Pressure",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.PRESSURE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Afterburner Heater sensors."""
    coordinator: AfterburnerCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities(
        AfterburnerSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class AfterburnerSensor(
    CoordinatorEntity[AfterburnerCoordinator], SensorEntity
):
    """Representation of an Afterburner Heater sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AfterburnerCoordinator,
        entry,
        description: SensorEntityDescription,
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
    def native_value(self):
        state = cast(HeaterState | None, self.coordinator.data)
        if state is None:
            return None
        if self.entity_description.key == "state_text":
            return state_text_from_raw(state.raw)
        if self.entity_description.key in state.raw:
            return state.raw[self.entity_description.key]
        return getattr(state, self.entity_description.key, None)
