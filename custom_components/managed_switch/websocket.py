"""WebSocket command for the switch card: one switch's ports with their entities and layout.

The card (managed-switch-card) asks for a device and draws its front panel; it needs to know which
entity belongs to which port and role, which entity IDs (that follow the user's language) do not
say reliably.

Every logged-in user may ask, as for entity states; the reply holds the switch's model, firmware
and port descriptions, no address or credentials. docs/card.md describes the reply.
"""

from __future__ import annotations

from typing import Any

from aiosnmpswitch.helpers import lag_members, port_name, uplink_ports
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
import probatio

from .const import DOMAIN
from .coordinator import SwitchConfigEntry, get_hub, switch_data
from .entity import entry_uid, firmware, model, ports, vendor

PORT_KEYS = {
    "link": "binary_sensor",
    "speed": "sensor",
    "device": "sensor",
    "poe": "sensor",
    "received": "sensor",
    "sent": "sensor",
    "errors": "sensor",
}
SWITCH_KEYS = {
    "boot_time": "sensor",
    "poe_consumption": "sensor",
    "poe_budget": "sensor",
    "port_event": "event",
}


@callback
def async_setup(hass: HomeAssistant) -> None:
    """Register the command."""
    websocket_api.async_register_command(hass, ws_ports)


def _entry_for_device(hass: HomeAssistant, device_id: str) -> SwitchConfigEntry | None:
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        return None
    entry = hass.config_entries.async_get_entry(device.config_entry_id)
    if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
        return None
    return entry


@websocket_api.websocket_command(
    {probatio.Required("type"): f"{DOMAIN}/ports", probatio.Required("device_id"): str}
)
@callback
def ws_ports(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return a switch, its ports and the entity of each port and role."""
    entry = _entry_for_device(hass, msg["device_id"])
    if entry is None:
        connection.send_error(msg["id"], "not_found", "No loaded managed switch with this device")
        return
    registry = er.async_get(hass)
    uid = entry_uid(entry)

    def entity_id(platform: str, unique_id: str) -> str | None:
        return registry.async_get_entity_id(platform, DOMAIN, unique_id)

    hub = get_hub(hass)
    data = switch_data(entry)
    uplinks = uplink_ports({k: switch_data(e) for k, e in hub.entries.items()}).get(
        entry.entry_id, set()
    )
    members = lag_members(data.lag_ports, data.interfaces)
    poe = entry.runtime_data.slow.data.poe
    poe_ports = {p.index for p in poe.ports} if poe else set()
    system = entry.runtime_data.slow.data.system
    chassis = entry.runtime_data.slow.data.chassis
    result_ports = []
    for interface in ports(entry):
        index = interface.index
        trunk_members = sorted(m for m, agg in members.items() if agg == index)
        result_ports.append(
            {
                "if_index": index,
                "name": port_name(interface),
                "alias": interface.alias,
                "kind": "trunk" if trunk_members else "ethernet",
                "trunk": members.get(index),
                "members": trunk_members,
                "uplink": index in uplinks or members.get(index) in uplinks,
                "poe": index in poe_ports,
                "entities": {
                    key: entity_id(platform, f"{uid}_{index}_{key}")
                    for key, platform in PORT_KEYS.items()
                },
            }
        )
    connection.send_result(
        msg["id"],
        {
            "switch": {
                "entry_id": entry.entry_id,
                "name": entry.title,
                "vendor": vendor(system),
                "model": model(system, chassis),
                "firmware": firmware(system, chassis),
                "object_id": system.object_id,
                "entities": {
                    key: entity_id(platform, f"{uid}_{key}")
                    for key, platform in SWITCH_KEYS.items()
                },
            },
            "ports": result_ports,
        },
    )
