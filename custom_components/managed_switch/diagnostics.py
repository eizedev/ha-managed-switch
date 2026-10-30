"""Diagnostics download: what the switch answers, without credentials or addresses."""

from __future__ import annotations

from collections import Counter
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_AUTH_KEY, CONF_COMMUNITY, CONF_PRIV_KEY, CONF_USER
from .coordinator import SwitchConfigEntry, get_hub
from .entity import ports

TO_REDACT = {CONF_HOST, CONF_COMMUNITY, CONF_USER, CONF_AUTH_KEY, CONF_PRIV_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SwitchConfigEntry
) -> dict[str, Any]:
    """Return counts and structure only; no MAC or IP addresses, names or descriptions."""
    slow, fast = entry.runtime_data.slow.data, entry.runtime_data.fast.data
    system = slow.system
    locations = [loc for loc in get_hub(hass).locations.values() if loc.switch == entry.entry_id]
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "system": {"descr": system.descr, "object_id": system.object_id},
        "temperatures": [
            {"name": t.name, "celsius": t.celsius, "status": t.status} for t in slow.temperatures
        ],
        "chassis": (
            {
                "descr": slow.chassis.descr,
                "model_name": slow.chassis.model_name,
                "software_rev": slow.chassis.software_rev,
            }
            if slow.chassis
            else None
        ),
        "interfaces": {
            "count": len(fast.interfaces),
            "types": dict(Counter(i.type for i in fast.interfaces.values())),
            "ports_with_entities": len(ports(entry)),
            "with_rates": len(fast.rates),
        },
        "address_table": len(slow.fdb),
        "bridge_ports": len(slow.bridge_ports),
        "lldp": {
            "chassis_id_subtype": slow.lldp.chassis_id_subtype if slow.lldp else None,
            "local_ports": len(slow.lldp.ports) if slow.lldp else 0,
            "neighbours": len(slow.lldp.remotes) if slow.lldp else 0,
        },
        "lag_rows": len(slow.lag_ports),
        "poe": {
            "supplies": len(slow.poe.supplies) if slow.poe else 0,
            "ports": len(slow.poe.ports) if slow.poe else 0,
        },
        "stp": slow.stp is not None,
        "neighbour_cache": len(slow.neighbors),
        "located_devices": len(locations),
        "ports_with_devices": len({loc.if_index for loc in locations}),
    }
