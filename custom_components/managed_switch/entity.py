"""Base entities: one device per switch, and entities per port of it."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aiosnmpswitch import Chassis, Interface, SystemInfo
from aiosnmpswitch.helpers import is_ethernet_port, lag_members, port_name
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, VENDORS
from .coordinator import SwitchConfigEntry, switch_data

_ENTERPRISE_PREFIX = "1.3.6.1.4.1."


def vendor(system: SystemInfo) -> str | None:
    """Return the vendor from the enterprise number in ``sysObjectID``, if known."""
    object_id = system.object_id or ""
    if not object_id.startswith(_ENTERPRISE_PREFIX):
        return None
    number = object_id.removeprefix(_ENTERPRISE_PREFIX).split(".", 1)[0]
    return VENDORS.get(int(number)) if number.isdigit() else None


def model(system: SystemInfo, chassis: Chassis | None = None) -> str | None:
    """Return the model: the ENTITY-MIB chassis's name, else ``sysDescr`` up to the first comma.

    ``sysDescr`` is "model, firmware, ..." on HPE and many others, but not on every vendor (Cisco
    starts with the operating system); the chassis entry names the product on its own.
    """
    if chassis is not None and (chassis.descr or chassis.model_name):
        return chassis.descr or chassis.model_name
    return system.descr.split(",", 1)[0].strip() if system.descr else None


def firmware(system: SystemInfo, chassis: Chassis | None = None) -> str | None:
    """Return the firmware: the chassis's software revision, else the 2nd part of ``sysDescr``."""
    if chassis is not None and chassis.software_rev:
        return chassis.software_rev
    if not system.descr or "," not in system.descr:
        return None
    return system.descr.split(",")[1].strip() or None


def url_host(host: str) -> str:
    """Return a host as it goes into a URL: IPv6 addresses in brackets."""
    return f"[{host}]" if ":" in host and not host.startswith("[") else host


def entry_uid(entry: SwitchConfigEntry) -> str:
    """Return the prefix of the entry's device identifier and entity unique IDs."""
    return entry.unique_id or entry.entry_id


def device_info(entry: SwitchConfigEntry) -> DeviceInfo:
    """Describe the switch of an entry for the device registry."""
    slow = entry.runtime_data.slow.data
    system = slow.system
    info = DeviceInfo(
        identifiers={(DOMAIN, entry_uid(entry))},
        manufacturer=vendor(system),
        model=model(system, slow.chassis),
        name=entry.title,
        sw_version=firmware(system, slow.chassis),
        configuration_url=f"http://{url_host(entry.data[CONF_HOST])}/",
    )
    if entry.unique_id:
        info["connections"] = {(CONNECTION_NETWORK_MAC, entry.unique_id)}
    return info


@callback
def async_add_per_port(
    entry: SwitchConfigEntry,
    coordinators: list[DataUpdateCoordinator[Any]],
    add: Callable[[list[Interface]], None],
    wanted: Callable[[Interface], bool] = lambda _: True,
) -> None:
    """Call ``add`` with the ports that have no entities yet, now and after every update.

    A trunk created later, or PoE ports read only after a failed first try, so get their
    entities without reloading the entry. Entities of ports that vanish stay, unavailable.
    """
    done: set[int] = set()

    @callback
    def _add_new() -> None:
        new = [i for i in ports(entry) if i.index not in done and wanted(i)]
        if new:
            done.update(i.index for i in new)
            add(new)

    _add_new()
    for coordinator in coordinators:
        entry.async_on_unload(coordinator.async_add_listener(_add_new))


def ports(entry: SwitchConfigEntry) -> list[Interface]:
    """Return the ports that get entities: Ethernet ports and trunks with members."""
    data = switch_data(entry)
    trunks = set(lag_members(data.lag_ports, data.interfaces).values())
    return [
        interface
        for index, interface in sorted(data.interfaces.items())
        if is_ethernet_port(interface) or index in trunks
    ]


class SwitchEntity[CoordinatorT: DataUpdateCoordinator[Any]](CoordinatorEntity[CoordinatorT]):
    """An entity of the switch itself."""

    _attr_has_entity_name = True

    def __init__(
        self, entry: SwitchConfigEntry, coordinator: CoordinatorT, description: EntityDescription
    ) -> None:
        """Bind the entity to its entry, coordinator and description."""
        super().__init__(coordinator)
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry_uid(entry)}_{description.key}"
        self._attr_device_info = device_info(entry)


class PortEntity[CoordinatorT: DataUpdateCoordinator[Any]](SwitchEntity[CoordinatorT]):
    """An entity of one port, named "Port <name> ..." through its translation."""

    def __init__(
        self,
        entry: SwitchConfigEntry,
        coordinator: CoordinatorT,
        description: EntityDescription,
        interface: Interface,
    ) -> None:
        """Bind the entity to its port by ``ifIndex``."""
        super().__init__(entry, coordinator, description)
        self.if_index = interface.index
        self._attr_unique_id = f"{entry_uid(entry)}_{interface.index}_{description.key}"
        self._attr_translation_placeholders = {"port": port_name(interface)}

    @property
    def interface(self) -> Interface | None:
        """The port's latest reading."""
        data = self.entry.runtime_data.fast.data
        return data.interfaces.get(self.if_index) if data else None

    @property
    def available(self) -> bool:
        """Available while the port is still reported."""
        return super().available and self.interface is not None
