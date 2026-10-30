"""Sensors of the switch and of each port."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aiosnmpswitch import Interface, OperStatus, PseDetectionStatus, PsePort
from aiosnmpswitch.helpers import port_name
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfDataRate, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .coordinator import (
    SIGNAL_LOCATIONS,
    FastCoordinator,
    FastData,
    SlowCoordinator,
    SlowData,
    SwitchConfigEntry,
)
from .devices import connected, summary
from .entity import PortEntity, SwitchEntity, async_add_per_port

PARALLEL_UPDATES = 0
POE_STATES = [state.name.lower() for state in PseDetectionStatus]


@dataclass(frozen=True, kw_only=True)
class SwitchSensorDescription(SensorEntityDescription):
    """A sensor of the switch, read from the slow coordinator."""

    value: Callable[[SlowData], datetime | int | None]
    exists: Callable[[SlowData], bool] = lambda data: True


def _poe_total(data: SlowData, field: str) -> int | None:
    supplies = data.poe.supplies if data.poe else []
    values = [getattr(s, field) for s in supplies if getattr(s, field) is not None]
    return sum(values) if values else None


SWITCH_SENSORS: tuple[SwitchSensorDescription, ...] = (
    SwitchSensorDescription(
        key="boot_time",
        translation_key="boot_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.boot_time,
    ),
    SwitchSensorDescription(
        key="poe_consumption",
        translation_key="poe_consumption",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: _poe_total(data, "consumption_power"),
        exists=lambda data: bool(data.poe and data.poe.supplies),
    ),
    SwitchSensorDescription(
        key="poe_budget",
        translation_key="poe_budget",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: _poe_total(data, "power"),
        exists=lambda data: bool(data.poe and data.poe.supplies),
    ),
    SwitchSensorDescription(
        key="topology_changes",
        translation_key="topology_changes",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value=lambda data: data.stp.top_changes if data.stp else None,
        exists=lambda data: data.stp is not None,
    ),
)


@dataclass(frozen=True, kw_only=True)
class PortSensorDescription(SensorEntityDescription):
    """A sensor of a port, read from the fast coordinator."""

    value: Callable[[Interface, FastData], float | int | None]


PORT_SENSORS: tuple[PortSensorDescription, ...] = (
    PortSensorDescription(
        key="speed",
        translation_key="speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        value=lambda port, _: port.high_speed if port.oper_status == 1 else 0,
    ),
    PortSensorDescription(
        key="received",
        translation_key="received",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value=lambda port, data: data.rates[port.index][0] if port.index in data.rates else None,
    ),
    PortSensorDescription(
        key="sent",
        translation_key="sent",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value=lambda port, data: data.rates[port.index][1] if port.index in data.rates else None,
    ),
    PortSensorDescription(
        key="errors",
        translation_key="errors",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value=lambda port, _: (
            None
            if port.in_errors is None and port.out_errors is None
            else (port.in_errors or 0) + (port.out_errors or 0)
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the switch's sensors and each port's."""
    runtime = entry.runtime_data
    entities: list[SensorEntity] = [
        SwitchSensor(entry, runtime.slow, description)
        for description in SWITCH_SENSORS
        if description.exists(runtime.slow.data)
    ]
    async_add_entities(entities)

    def add_port_sensors(new: list[Interface]) -> None:
        port_entities: list[SensorEntity] = []
        for interface in new:
            port_entities += [PortSensor(entry, runtime.fast, d, interface) for d in PORT_SENSORS]
            port_entities.append(DeviceSensor(entry, runtime.fast, interface))
        async_add_entities(port_entities)

    def is_poe_port(interface: Interface) -> bool:
        poe = runtime.slow.data.poe
        return poe is not None and any(p.index == interface.index for p in poe.ports)

    coordinators: list[DataUpdateCoordinator[Any]] = [runtime.fast, runtime.slow]
    async_add_per_port(entry, coordinators, add_port_sensors)
    async_add_per_port(
        entry,
        coordinators,
        lambda new: async_add_entities(PoeSensor(entry, runtime.slow, i) for i in new),
        is_poe_port,
    )


class SwitchSensor(SwitchEntity[SlowCoordinator], SensorEntity):
    """A sensor of the switch itself."""

    entity_description: SwitchSensorDescription

    @property
    def native_value(self) -> datetime | int | None:
        """The value from the latest tables."""
        return self.entity_description.value(self.coordinator.data)


class PortSensor(PortEntity[FastCoordinator], SensorEntity):
    """Speed, traffic or errors of one port."""

    entity_description: PortSensorDescription

    @property
    def native_value(self) -> float | int | None:
        """The value from the latest reading."""
        interface = self.interface
        return (
            self.entity_description.value(interface, self.coordinator.data) if interface else None
        )


class DeviceSensor(PortEntity[FastCoordinator], SensorEntity):
    """What is connected to a port: one name, or the first name and how many more."""

    # The port's link and speed are here too, so a dashboard needs only this sensor; they have
    # their own entities with history, so they are not recorded twice.
    _unrecorded_attributes = frozenset({"devices", "port", "if_index", "link", "speed"})

    def __init__(
        self, entry: SwitchConfigEntry, coordinator: FastCoordinator, interface: Interface
    ) -> None:
        """Describe the sensor for its port."""
        super().__init__(
            entry,
            coordinator,
            SensorEntityDescription(key="device", translation_key="device"),
            interface,
        )

    async def async_added_to_hass(self) -> None:
        """Update when the devices are located again."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_LOCATIONS, self.async_write_ha_state)
        )

    @property
    def native_value(self) -> str | None:
        """The first device's name, with the number of others."""
        return summary(connected(self.hass, self.entry, self.if_index))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """All devices on the port, with MAC and IP addresses; the port's name, link and speed."""
        devices = connected(self.hass, self.entry, self.if_index)
        interface = self.interface
        assert interface is not None  # noqa: S101 - unavailable otherwise, attributes not read
        return {
            "device_count": len(devices),
            "devices": [d.as_dict() for d in devices],
            "port": port_name(interface),
            "if_index": self.if_index,
            "link": interface.oper_status is OperStatus.UP,
            "speed": interface.high_speed if interface.oper_status is OperStatus.UP else 0,
        }


class PoeSensor(PortEntity[SlowCoordinator], SensorEntity):
    """PoE state of one port: searching, delivering power, fault, ..."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = POE_STATES

    def __init__(
        self, entry: SwitchConfigEntry, coordinator: SlowCoordinator, interface: Interface
    ) -> None:
        """Describe the sensor for its port."""
        super().__init__(
            entry, coordinator, SensorEntityDescription(key="poe", translation_key="poe"), interface
        )

    def _port(self) -> PsePort | None:
        poe = self.coordinator.data.poe
        return next((p for p in poe.ports if p.index == self.if_index), None) if poe else None

    @property
    def native_value(self) -> str | None:
        """The detection status, lower case."""
        port = self._port()
        if port is None or port.detection_status is None:
            return None
        return port.detection_status.name.lower()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Whether PoE is enabled on the port, and the powered device's class."""
        port = self._port()
        if port is None:
            return {}
        classes = port.power_classifications
        return {
            "enabled": port.admin_enable,
            "power_class": classes - 1 if classes is not None else None,
        }
