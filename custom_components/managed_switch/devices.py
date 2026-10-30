"""What is connected to a port: LLDP neighbours and located devices, named from the registry."""

from __future__ import annotations

from dataclasses import dataclass

from aiosnmpswitch.helpers import neighbors_by_port
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .coordinator import SwitchConfigEntry, get_hub, switch_data


@dataclass(frozen=True, slots=True)
class Connected:
    """One device on a port."""

    mac: str | None
    name: str | None
    ip_addresses: tuple[str, ...] = ()
    lldp: bool = False
    """Whether the device announced itself by LLDP (a switch, access point, phone, ...)."""

    def as_dict(self) -> dict[str, object]:
        """Return the device as a state attribute."""
        return {
            "mac": self.mac,
            "name": self.name,
            "ip_addresses": list(self.ip_addresses),
            "lldp": self.lldp,
        }


def registry_name(hass: HomeAssistant, mac: str) -> str | None:
    """Return the name Home Assistant knows a MAC address by (not from this integration)."""
    devices = dr.async_get(hass).async_get_devices(connections={(dr.CONNECTION_NETWORK_MAC, mac)})
    names = [
        device.name_by_user or device.name
        for device in devices
        if not any(domain == DOMAIN for domain, _ in device.identifiers)
    ]
    # Several integrations may know the MAC address: take one name, the same every time.
    return min((n for n in names if n), default=None, key=lambda n: n.casefold())


def connected(hass: HomeAssistant, entry: SwitchConfigEntry, if_index: int) -> list[Connected]:
    """Return the devices on one port: LLDP neighbours first, then located devices by name."""
    result: list[Connected] = []
    seen: set[str] = set()
    data = switch_data(entry)
    for remote in neighbors_by_port(data).get(if_index, []):
        mac = remote.chassis_id if remote.chassis_id_subtype == 4 else None  # noqa: PLR2004
        name = remote.sys_name or (registry_name(hass, mac) if mac else None)
        result.append(Connected(mac, name, remote.management_addresses, lldp=True))
        if mac:
            seen.add(mac)
    located = [
        loc
        for loc in get_hub(hass).locations.values()
        if loc.switch == entry.entry_id and loc.if_index == if_index and loc.address not in seen
    ]
    devices = [
        Connected(loc.address, registry_name(hass, loc.address), loc.ip_addresses)
        for loc in located
    ]
    devices.sort(key=lambda d: (d.name is None, (d.name or "").casefold(), d.mac or ""))
    return result + devices


def summary(devices: list[Connected]) -> str | None:
    """Return the device sensor's state: the first name, and how many more there are."""
    if not devices:
        return None
    first = devices[0].name or devices[0].mac or "?"
    return first if len(devices) == 1 else f"{first} +{len(devices) - 1}"
