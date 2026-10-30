"""Link of each port."""

from __future__ import annotations

from aiosnmpswitch import OperStatus
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import FastCoordinator, SwitchConfigEntry
from .entity import PortEntity, ports

PARALLEL_UPDATES = 0
LINK = BinarySensorEntityDescription(
    key="link", translation_key="link", device_class=BinarySensorDeviceClass.CONNECTIVITY
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a link sensor per port."""
    async_add_entities(
        LinkSensor(entry, entry.runtime_data.fast, LINK, interface) for interface in ports(entry)
    )


class LinkSensor(PortEntity[FastCoordinator], BinarySensorEntity):
    """On while the port has a link."""

    @property
    def is_on(self) -> bool | None:
        """Whether ``ifOperStatus`` is up."""
        interface = self.interface
        if interface is None or interface.oper_status is None:
            return None
        return interface.oper_status is OperStatus.UP
