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


# Integrations whose devices are the internet gateway itself: UPnP (IGD) has one device, the router.
GATEWAY_DOMAINS = frozenset({"upnp"})


def _registry_devices(hass: HomeAssistant, mac: str) -> list[dr.DeviceEntry]:
    """Return the devices of other integrations that know this MAC address."""
    devices = dr.async_get(hass).async_get_devices(connections={(dr.CONNECTION_NETWORK_MAC, mac)})
    return [d for d in devices if not any(domain == DOMAIN for domain, _ in d.identifiers)]


def _name(devices: list[dr.DeviceEntry]) -> str | None:
    """Pick one name, the same every time, when several integrations know a MAC address."""
    names = [device.name_by_user or device.name for device in devices]
    return min((n for n in names if n), default=None, key=lambda n: n.casefold())


def registry_name(hass: HomeAssistant, mac: str) -> str | None:
    """Return the name Home Assistant knows a MAC address by (not from this integration)."""
    return _name(_registry_devices(hass, mac))


def _is_gateway(hass: HomeAssistant, devices: list[dr.DeviceEntry]) -> bool:
    for device in devices:
        for entry_id in device.config_entries:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry is not None and entry.domain in GATEWAY_DOMAINS:
                return True
    return False


def connected(hass: HomeAssistant, entry: SwitchConfigEntry, if_index: int) -> list[Connected]:
    """Return the devices on one port, the one that best names the port first.

    Order: LLDP neighbours; the internet gateway (a device of the UPnP integration); a device
    other devices on the port are linked to (``via_device``, such as an access point); then the
    rest by name.
    """
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
    registry = {loc.address: _registry_devices(hass, loc.address) for loc in located}
    parents = {d.via_device_id for devices in registry.values() for d in devices if d.via_device_id}

    def rank(mac: str) -> int:
        devices = registry[mac]
        if _is_gateway(hass, devices):
            return 0
        return 1 if any(d.id in parents for d in devices) else 2

    devices = sorted(
        (
            (
                rank(loc.address),
                Connected(loc.address, _name(registry[loc.address]), loc.ip_addresses),
            )
            for loc in located
        ),
        key=lambda item: (
            item[0],
            item[1].name is None,
            (item[1].name or "").casefold(),
            item[1].mac or "",
        ),
    )
    return result + [device for _, device in devices]


def summary(devices: list[Connected]) -> str | None:
    """Return the device sensor's state: the first name, and how many more there are."""
    if not devices:
        return None
    first = devices[0].name or devices[0].mac or "?"
    return first if len(devices) == 1 else f"{first} +{len(devices) - 1}"
