"""Support for xiaomi ble sensors."""

from __future__ import annotations

import logging

from sensor_state_data import DeviceClass, SensorUpdate, Units

from homeassistant import config_entries
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataUpdate,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfMass,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.sensor import sensor_device_info_to_hass_device_info

from .const import DOMAIN
from .device import device_key_to_bluetooth_entity_key
from .RenphoActiveBluetoothProcessorCoordinator import (
    RenphoActiveBluetoothProcessorCoordinator,
    RenphoPassiveBluetoothDataProcessor,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS = {
    ("weight", Units.MASS_GRAMS): SensorEntityDescription(
        key=f"{"weight"}_{Units.MASS_GRAMS}",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (
        DeviceClass.SIGNAL_STRENGTH,
        Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    ): SensorEntityDescription(
        key=f"{DeviceClass.SIGNAL_STRENGTH}_{Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT}",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


def sensor_update_to_bluetooth_data_update(
    sensor_update: SensorUpdate,
) -> PassiveBluetoothDataUpdate:
    """Convert a sensor update to a bluetooth data update."""
    _LOGGER.warning("***+++ sensor_update_to_bluetooth_data_update:%s", sensor_update)
    for device_id, device_info in sensor_update.devices.items():
        _LOGGER.warning(
            "*** device_id %s:%s",
            device_id,
            sensor_device_info_to_hass_device_info(device_info),
        )

    # PassiveBluetoothEntityKey(key='temperature', device_id=None):Temperature
    for device_key, sensor_values in sensor_update.entity_values.items():
        _LOGGER.warning(
            "*** entity_names %s:%s",
            device_key_to_bluetooth_entity_key(device_key),
            sensor_values.name,
        )

    return PassiveBluetoothDataUpdate(
        # (title=None, anufacturer=None, sw_version='123456', hw_version=None)},
        # devices={None: SensorDeviceInfo(name=None, model=None, manufacturer=None, sw_version='123456', hw_version=None)}
        devices={
            device_id: sensor_device_info_to_hass_device_info(device_info)
            for device_id, device_info in sensor_update.devices.items()
        },
        # entity_descriptions={DeviceKey(key='battery', device_id=None): SensorDescription(device_key=DeviceKey(key='battery', device_id=None), device_class=<SensorDeviceClass.BATTERY: 'battery'>, native_unit_of_measurement=<Units.PERCENTAGE: '%'>)},
        entity_descriptions={
            device_key_to_bluetooth_entity_key(device_key): SENSOR_DESCRIPTIONS[
                (description.device_class, description.native_unit_of_measurement)
            ]
            for device_key, description in sensor_update.entity_descriptions.items()
            if description.device_class
        },
        entity_data={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.native_value
            for device_key, sensor_values in sensor_update.entity_values.items()
        },
        # entity_values={DeviceKey(key='battery', device_id=None): SensorValue(device_key=DeviceKey(key='battery', device_id=None), name='Battery', native_value=99)}
        entity_names={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.name
            for device_key, sensor_values in sensor_update.entity_values.items()
        },
        # devices={
        #     device_id: sensor_device_info_to_hass_device_info(device_info)
        #     for device_id, device_info in sensor_update.devices.items()
        # },
        # entity_descriptions={
        #     device_key_to_bluetooth_entity_key(device_key): SENSOR_DESCRIPTIONS[
        #         (description.device_class, description.native_unit_of_measurement)
        #     ]
        #     for device_key, description in sensor_update.entity_descriptions.items()
        #     if description.device_class
        # },
        # entity_data={
        #     device_key_to_bluetooth_entity_key(device_key): sensor_values.native_value
        #     for device_key, sensor_values in sensor_update.entity_values.items()
        # },
        # entity_names={
        #     device_key_to_bluetooth_entity_key(device_key): sensor_values.name
        #     for device_key, sensor_values in sensor_update.entity_values.items()
        # },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Xiaomi BLE sensors."""
    _LOGGER.warning("*** sensor async_setup_entry:%s", entry)
    coordinator: RenphoActiveBluetoothProcessorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    processor = RenphoPassiveBluetoothDataProcessor(
        sensor_update_to_bluetooth_data_update
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(
            RenphoBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, SensorEntityDescription)
    )


class RenphoBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[RenphoPassiveBluetoothDataProcessor],
    SensorEntity,
):
    """Representation of a xiaomi ble sensor."""

    @property
    def native_value(self) -> int | float | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available
