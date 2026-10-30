"""The Managed Switch (SNMP) integration: managed network switches, read only."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aiosnmpswitch import (
    AuthProtocol,
    CommunityAuth,
    PrivProtocol,
    PysnmpTransport,
    SnmpError,
    SnmpSwitch,
    UsmAuth,
)
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

# Loaded here, while Home Assistant imports the integration outside the event loop: pysnmp reads
# many modules on first use.
import pysnmp.hlapi.v3arch.asyncio  # noqa: F401

from .const import (
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SNMP_VERSION,
    CONF_USER,
    DEFAULT_PORT,
    DOMAIN,
    REQUEST_RETRIES,
    REQUEST_TIMEOUT,
)
from .coordinator import (
    FastCoordinator,
    SlowCoordinator,
    SwitchConfigEntry,
    SwitchRuntimeData,
    get_hub,
    map_error,
)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.EVENT, Platform.SENSOR]


def auth_from(data: Mapping[str, Any]) -> CommunityAuth | UsmAuth:
    """Credentials from an entry's data."""
    if data[CONF_SNMP_VERSION] in ("1", "2c"):
        return CommunityAuth(data[CONF_COMMUNITY], version=data[CONF_SNMP_VERSION])
    return UsmAuth(
        data[CONF_USER],
        data.get(CONF_AUTH_KEY) or None,
        data.get(CONF_PRIV_KEY) or None,
        auth_protocol=AuthProtocol(data.get(CONF_AUTH_PROTOCOL, AuthProtocol.SHA)),
        priv_protocol=PrivProtocol(data.get(CONF_PRIV_PROTOCOL, PrivProtocol.AES128)),
    )


async def connect(data: Mapping[str, Any]) -> SnmpSwitch:
    """Create a client for the switch an entry's data describes."""
    transport = await PysnmpTransport.create(
        data[CONF_HOST],
        auth_from(data),
        port=int(data.get(CONF_PORT, DEFAULT_PORT)),
        timeout=REQUEST_TIMEOUT,
        retries=REQUEST_RETRIES,
    )
    return SnmpSwitch(transport)


async def async_setup_entry(hass: HomeAssistant, entry: SwitchConfigEntry) -> bool:
    """Connect to one switch and start polling it."""
    try:
        switch = await connect(entry.data)
    except SnmpError as err:
        raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="resolve") from err
    fast = FastCoordinator(hass, entry, switch)
    slow = SlowCoordinator(hass, entry, switch)
    entry.runtime_data = SwitchRuntimeData(switch=switch, fast=fast, slow=slow)
    try:
        await slow.async_config_entry_first_refresh()
        await fast.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed, ConfigEntryNotReady:
        await switch.close()
        raise
    hub = get_hub(hass)
    await hub.async_load()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hub.async_add(entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SwitchConfigEntry) -> bool:
    """Stop polling and release the SNMP engine."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        get_hub(hass).async_remove(entry)
        await entry.runtime_data.switch.close()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: SwitchConfigEntry) -> None:
    """Forget the located devices once no switch is left."""
    if not any(e.entry_id != entry.entry_id for e in hass.config_entries.async_entries(DOMAIN)):
        await get_hub(hass).async_forget()


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: SwitchConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Keep the switch's own device while the entry is set up."""
    return False


__all__ = ["auth_from", "connect", "map_error"]
