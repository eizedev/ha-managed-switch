"""Made-up devices with the MAC addresses of the test data, so the demo shows names.

Only for scripts/demo/run.py; it stands in for the integrations (router, Wi-Fi, TV, ...) that
know these devices in a real Home Assistant.
"""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

DOMAIN = "demo_devices"

# MAC address (anonymized test data) -> name; a parent's clients are linked to it (via_device).
ROUTER = "02:00:00:00:00:06"
ACCESS_POINT = "02:00:00:00:00:03"
DEVICES = {
    ROUTER: "Router",
    "02:00:00:00:00:09": "Kitchen tablet",
    "02:00:00:00:00:0c": "Phone (Alex)",
    "02:00:00:00:00:0e": "Phone (Sam)",
    "02:00:00:00:00:0f": "Watch (Alex)",
    "02:00:00:00:00:10": "Robot vacuum",
    "02:00:00:00:00:13": "Office speaker",
    "02:00:00:00:00:15": "Bathroom speaker",
    "02:00:00:00:00:16": "Coffee machine",
    "02:00:00:00:00:1b": "Work laptop",
    "02:00:00:00:00:1c": "Window controller",
    "02:00:00:00:00:1d": "Laptop (Sam)",
    "02:00:00:00:00:20": "E-reader",
    "02:00:00:00:00:26": "Smart plug",
    "02:00:00:00:00:04": "NAS",
    "02:00:00:00:00:05": "NAS (backup link)",
    "02:00:00:00:00:08": "Server",
    "02:00:00:00:00:1e": "Home Assistant",
    "02:00:00:00:00:1f": "Server (management)",
    ACCESS_POINT: "Access point",
    "02:00:00:00:00:07": "Tablet (Alex)",
    "02:00:00:00:00:0d": "Living room speaker",
    "02:00:00:00:00:11": "Phone (guest)",
    "02:00:00:00:00:14": "Thermostat",
    "02:00:00:00:00:17": "Camera (garden)",
    "02:00:00:00:00:18": "Doorbell",
    "02:00:00:00:00:21": "Laptop (Alex)",
    "02:00:00:00:00:27": "Weather station",
    "02:00:00:00:00:22": "Smart home hub",
    "02:00:00:00:00:23": "Light bridge",
    "02:00:00:00:00:25": "Living room TV",
    "02:00:00:00:00:32": "Game console",
    "02:00:00:00:00:12": "Media player",
    "02:00:00:00:00:24": "Desktop",
    "02:00:00:00:00:28": "Printer",
}
PARENTS = {
    ROUTER: list(DEVICES)[1:14],
    ACCESS_POINT: list(DEVICES)[20:28],
}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Create the config entry that owns the made-up devices."""
    if not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_IMPORT})
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Register the devices with their MAC addresses."""
    registry = dr.async_get(hass)
    ids = {
        mac: registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, mac)},
            name=name,
        ).id
        for mac, name in DEVICES.items()
    }
    for parent, children in PARENTS.items():
        for child in children:
            registry.async_update_device(ids[child], via_device_id=ids[parent])
    return True
